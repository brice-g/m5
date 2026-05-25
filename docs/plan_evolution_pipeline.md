# Plan d'Évolution de la Pipeline de Traitement FastIA

Ce document cadre l'évolution technique de la pipeline de données FastIA pour intégrer l'enrichissement sémantique (détection de la langue et analyse de sentiment) sans régressions sur le socle existant.

---

## 1. Schéma Cible d'Architecture

Les étapes d'enrichissement (`enrich_language` et `enrich_sentiment`) s'insèrent **juste après la phase de nettoyage (Cleaning) et immédiatement avant le moteur de règles métier et le stockage en base de données**.

### Logique de placement :
* **Après le Cleaning :** Les modèles de NLP (`fasttext` ou `transformers`) sont sensibles aux bruits textuels (balises HTML, sauts de lignes multiples, signatures complexes). Travailler sur un texte standardisé et nettoyé (`input_text`) maximise la précision de l'inférence.
* **Avant les règles métier et le modèle M1 :** La langue détectée et le niveau de mécontentement sont des variables d'entrée critiques pour le routage et le calcul de la priorité finale. Ils doivent donc être calculés *en amont* des décisions logiques.

### Flux de données séquentiel :
```text
[Sources Entrantes] (Mbox, CSV Chat, JSONL Web)
        │
        ▼
[Loaders Spécifiques] (src.sources.*) --> Extraction en RawDemande
        │
        ▼
[Cleaning Pipeline] (src.pipeline.clean) --> Génération de input_text (sans HTML, normalisé)
        │
        ▼
========================================================================
[NOUVEAU SOCLE : ENRICHISSEMENT] (src.pipeline.enrich)
  ├── 1. enrich_language  --> Détermine 'langue' & 'langue_confidence'
  └── 2. enrich_sentiment --> Détermine 'sentiment' & 'sentiment_score'
========================================================================
        │
        ▼
[Moteur de Règles & Modèle M1] --> Calcul Catégorie, Ajustement Priorité Opérationnelle
        │
        ▼
[Persistence Layer] --> Insertion SQL finale dans la table 'public.demandes'

```

## 2. Évolution du Schéma SQL (Migration Alembic)

La table `public.demandes` possède déjà historiquement une colonne `langue`. L'évolution nécessite l'ajout des métriques de confiance et des dimensions liées à l'analyse de sentiment.

### Nouvelles colonnes à ajouter :
* `langue_confidence` (`NUMERIC` / `FLOAT`, *nullable*) : Score de certitude du modèle.
* `sentiment` (`VARCHAR(20)`, *nullable*) : Label binaire ou multiniveau extrait (Mécontent, Neutre/Satisfait).
* `sentiment_score` (`NUMERIC` / `FLOAT`, *nullable*) : Probabilité ou score de confiance associé à la prédiction de sentiment.

### Proposition du script de migration Alembic (`migrations/versions/xxxx_add_enrichment_columns.py`) :

```python
"""add enrichment columns

Revision ID: xxxx_add_enrichment_columns
Revises: 
Create Date: 2026-05-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'xxxx_add_enrichment_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('demandes', sa.Column('langue_confidence', sa.Float(), nullable=True))
    op.add_column('demandes', sa.Column('sentiment', sa.String(length=20), nullable=True))
    op.add_column('demandes', sa.Column('sentiment_score', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('demandes', 'sentiment_score')
    op.drop_column('demandes', 'sentiment')
    op.drop_column('demandes', 'langue_confidence')

```

### 3. Impact sur le Modèle FastIA M1 & Logique Métier

Une question centrale se pose : Faut-il réentraîner le modèle de classification/priorisation M1 ou modifier son prompt pour intégrer ces nouvelles variables ?

#### Décision stratégique : Règle métier déterministe en post-prédiction (Post-processing)
Plutôt que de modifier le modèle prédictif M1, nous appliquons une couche algorithmique de post-traitement. Cette approche est privilégiée pour trois raisons majeures :

* **Coût et Complexité Nuls :** Modifier un prompt ou réentraîner un modèle engendre une phase de non-régression lourde. Une règle de code python (`if/else`) s'exécute en une fraction de microseconde sans coût de token ou de calcul.
* **Auditabilité Totale :** Le métier peut précisément comprendre et ajuster pourquoi un ticket est passé en priorité critique (ex: *« Si Langue != FR et Sentiment = Mécontent sur le canal Web, alors Priorité = HAUTE »*). Un modèle de Deep Learning rend cette règle probabiliste et opaque.
* **Découplage applicatif :** Le modèle M1 reste concentré sur sa tâche principale (catégorisation thématique du contenu textuel), tandis que le routeur gère la cinématique de distribution opérationnelle.

#### Exemple d'implémentation de la logique de post-traitement :

```python
def adjust_demande_priority(demande_data: dict) -> str:
    """Ajuste la priorité calculée par M1 selon les enrichissements linguistiques et sémantiques."""
    base_priority = demande_data.get("priorite", "normale")
    canal = demande_data.get("canal")
    langue = demande_data.get("langue")
    sentiment = demande_data.get("sentiment")

    # Règle métier 1 : Routage international critique sur le Web/Chat
    if canal in ["web", "chat"] and langue in ["en", "es"] and sentiment == "Mécontent":
        return "haute"  # Escalade immédiate vers l'équipe internationale dédiée

    # Règle métier 2 : Alerte de sévérité globale
    if sentiment == "Mécontent" and base_priority == "basse":
        return "moyenne" # On rehausse le niveau minimal d'attention

    return base_priority
```
### 4. Roadmap de Déploiement Proposée

L'intégration industrielle de ces briques est découpée de manière incrémentale afin de valider chaque composant sans perturber le flux de production existant.

#### Phase 1 : Preuve de Concept et Validation Empirique (Module 3 - Actuel)
* **Objectifs :** Évaluation des sources de données, validation de la distribution réelle (infirmation du tiers non-FR global, validation sur le canal Web), correction des formats de sortie des Transformers Hugging Face.
* **Livrables :** `notebook_brief3_module3.ipynb`, `sources_data_evaluation.md`, `plan_evolution_pipeline.md`.

#### Phase 2 : Développement du Module d'Enrichissement Isolé (Fin de Module 3)
* **Objectifs :** Création du fichier `src/pipeline/enrich.py` contenant les fonctions autonomes d'appel aux modèles locaux (`fasttext` pour la langue, `distilcamembert` pour le sentiment).
* **Vigilance technique :** Implémentation de tests unitaires rigoureux avec `pytest` simulant des entrées malformées, des textes vides ou des chaînes de caractères ultra-courtes pour valider le comportement des fallbacks de secours.

#### Phase 3 : Migration et Activation Conditionnelle (Début de Module 4)
* **Objectifs :** Application de la migration de structure de base de données via Alembic en production. Connexion de l'étape d'enrichissement au sein du workflow général.
* **Optimisation d'éco-conception :** Mise en place d'une activation conditionnelle de l'étape `enrich_language` uniquement si le canal est web ou chat, évitant ainsi d'exécuter des calculs CPU/GPU superflus sur le flux email qui est validé comme 100 % francophone.

#### Phase 4 : Industrialisation et Moteur de Règles Métier (Module 4)
* **Objectifs :** Déploiement de la fonction de post-traitement pour la sur-priorisation des messages internationaux insatisfaits. Monitoring des temps de latence de la pipeline globale et mise en place d'un tableau de bord de supervision des taux d'erreur de prédiction (dérive de modèle).