## Module 4 — Brief 1 : Benchmark et Robustesse de la Pipeline FastIA

Cette section résume le protocole d'évaluation, les métriques clés obtenues après exécution et l'analyse de robustesse menée sur les composants d'enrichissement de la pipeline FastIA.

---

### 1. Protocole d'Évaluation
* **Détection de Langue** : Évaluation sur un jeu de données de **200 exemples** annotés à la main (`langue_eval_200.jsonl`).
* **Analyse de Sentiment** : Évaluation sur un jeu de données ciblé de **50 exemples** en français (`sentiment_eval_50.jsonl`) annotés manuellement, couvrant les trois canaux (email, web, chat).

### 2. Synthèse des Résultats Clés (Benchmarks)

#### A. Composant Détection de Langue
Le modèle **FastText (LID)** s'impose comme le choix de production incontestable en affichant un équilibre parfait entre performance pure, vélocité et éco-conception.

* **Précision (Accuracy)** : FastText et XLM-RoBERTa atteignent tous deux un score parfait de **100.0%** sur notre jeu de test, surpassant la baseline `langdetect` (**98.0%**).
* **Vitesse et Latence** : FastText est le plus véloce avec une latence infime de **~0.03 ms/doc**, ce qui le rend **~220 fois plus rapide** que `langdetect` (6.73 ms) et élimine le goulot d'étranglement des Transformers (>150 ms).
* **Empreinte Ressource (RAM)** : Consommation de **< 1 MB** pour FastText, contre **60.5 MB** pour `langdetect` et plus de **1.2 GB** pour le modèle Transformer.

#### B. Composant Analyse de Sentiment
Le modèle distillé **DistilCamembert** surclasse nettement l'approche multilingue globale pour notre besoin centré sur le français.

* **Précision** : DistilCamembert obtient un F1-Score robuste de **0.89** face aux nuances textuelles, là où BERT Multilingual s'effondre à **0.52 (52%) d'accuracy** sur ce sous-ensemble.
* **Performance Opérationnelle** : DistilCamembert est plus léger (~260 MB contre ~700 MB) et évite la latence excessive induite par BERT Multilingual (**106.47 ms/doc**).

---

### 3. Modèle de Menace (Threat Modeling) & Robustesse
Conformément aux frameworks **MITRE ATLAS** et **NIST**, la pipeline a été confrontée à des attaques adversariales :

* **Attaques par Homoglyphes (Visual Mimicry)** : La baseline `langdetect` s'est fait piéger systématiquement (0% de réussite). FastText démontre une robustesse moyenne mais reste vulnérable. 
* **Bruit Typo & Injections** : Les modèles de sentiment (Transformers) perdent en fiabilité face au bruit agressif et aux surcharges de mots-clés.
* **Remédiations Intégrées** : 
  1. Implémentation d'un **Sanitizer en amont** (Normalisation Unicode NFKC) pour désamorcer les homoglyphes avant l'inférence.
  2. Configuration d'un **Seuil de confiance à 0.70** avec mécanisme de **Fallback Humain** (routage vers une file d'attente manuelle en cas d'incertitude).

---

### 4. Conditions de Remise en Question de l'Architecture
L'architecture validée (**FastText + DistilCamembert**) sera réévaluée si l'un des seuils de production suivants est franchi :
* **Volume de charge** : Si le trafic global dépasse **100 000 requêtes / jour** (réévaluation des coûts de calcul CPU/GPU pour le sentiment).
* **Évolution du flux** : Si les messages très courts (< 20 caractères) représentent plus de **25% du flux entrant** (limite de précision de FastText).
* **Indicateur de menace** : Si le taux d'homoglyphes ou de caractères suspects détectés par le sanitizer dépasse **5% du trafic quotidien** (nécessité de durcir la sécurité périphérique).

---

## Module 4 — Brief 2 : Architecture et Dossier de Conception FastIA

Cette section présente la vue d'ensemble du dossier de conception technique complet exigé par le CTO avant le lancement des développements. Elle décrit l'architecture cible enrichie, la stratégie de sécurité périmétrique, les contrats d'interfaces d'API et la planification du déploiement.

### 1. Cartographie du Dossier de Conception (Livrables)

Le dossier technique est structuré autour des livrables clés suivants, garantissant qu'une équipe de développement puisse reprendre et implémenter la suite du projet en totale autonomie :

* **`docs/architecture_cible.md`** : Diagramme Mermaid complet et registre des composants de la pipeline (Loaders $\rightarrow$ Sanitizer $\rightarrow$ Cache $\rightarrow$ Inférence $\rightarrow$ Routage $\rightarrow$ BDD).
* **`src/security/input_sanitizer.py`** : Module Python de nettoyage défensif (normalisation Unicode NFKC, détection heuristique d'injections et troncature de surface) validé par sa suite de tests unitaires (`tests/test_input_sanitizer.py`).
* **`alembic/versions/xxx_add_enrichment_columns.py`** (ou `docs/migration_enrichment.sql`) : Script DDL de migration de base de données PostgreSQL rétrocompatible (`nullable=True`) avec indexation de performance.
* **`docs/spec_api_enrichie.md`** : Contrat d'interface et schémas Pydantic (`src/api/schemas.py`) mettant à jour `/predict` et exposant les nouveaux points d'accès (`POST /enrich`, `GET /models`).
* **`docs/risques_ethiques.md`** : Volet d'analyse éthique consolidé face aux biais de modèles et mise en conformité réglementaire (**RGPD Art. 22** et **AI Act Art. 5**).
* **`docs/plan_attenuation.md`** : Matrice opérationnelle des contre-mesures face aux attaques du *Threat Model* (Homoglyphes, Injections, Empoisonnement, Extraction).
* **`docs/plan_mise_en_oeuvre.md`** : Feuille de route (Roadmap) d'intégration incrémentale découpée en 3 phases sur 5 sprints de développement.
* **`docs/model_card_langue.md`** : Documentation officielle du composant de détection de langue FastText selon le standard de Mitchell et al. (2019).

---

### 2. Synthèse de l'Architecture Cible

L'architecture cible s'appuie sur une approche d'**inférence en cascade éco-conçue**, positionnant un système de cache de données en amont des modèles d'intelligence artificielle les plus lourds.

1.  **Défense Périmétrique & Détection** : Les requêtes brutes issues des Loaders sont nettoyées par le `Sanitizer`. Une empreinte numérique (Hash MD5) du corps du texte est générée pour interroger le cache.
2.  **Gestion du Cache (Éco-conception)** : 
    * *Cache Hit* : Récupération instantanée des scores existants en base de données (**< 1 ms**, consommation CPU nulle).
    * *Cache Miss* : Déclenchement de l'inférence. Le modèle ultra-léger FastText traite le document. Si et seulement si la langue détectée est le Français (`fr`), le texte est transmis au transformeur `DistilCamembert` pour l'analyse de sentiment.
3.  **Triage et Routage Prioritaire** : Dès la persistance des scores en BDD PostgreSQL, un moteur de routage métier aiguille les demandes :
    * `langue != 'fr'` $\rightarrow$ File d'attente internationale prioritaires (`high_intl`).
    * `sentiment == 'negatif'` (Confiance $> 0.80$) $\rightarrow$ File d'attente d'urgence CRM (`high_negative`).
    * Autres flux $\rightarrow$ Flux d'agent standard (`normal`).

---

### 3. Trajectoire de Déploiement (Plan de mise en œuvre)

Le déploiement industriel s'articule autour de 3 phases successives visant à garantir le maintien en conditions opérationnelles (MCO) de la production actuelle :

* **Phase 1 — Composant Langue (Sprints 1-2)** : Migration SQL $\rightarrow$ Intégration du modèle FastText $\rightarrow$ Script de Backfill par lots de l'historique $\rightarrow$ Exposition des dimensions de langue sur `/predict`.
* **Phase 2 — Composant Sentiment (Sprints 3-4)** : Intégration de DistilCamembert conditionnée au flux francophone $\rightarrow$ Backfill sentiment $\rightarrow$ Activation du cache d'enrichissement $\rightarrow$ Monitoring de la distribution des classes.
* **Phase 3 — Routage Prioritaire & Finitions (Sprint 5)** : Implémentation du moteur d'aiguillage $\rightarrow$ Intégration des middlewares de sécurité et Rate Limiting $\rightarrow$ Déploiement des endpoints standalone et du dashboard de suivi des volumes pour le management métier.

## Module 5 — Brief 1 : Déploiement & Industrialisation

### 1. Migration de la Base de Données (SQL)

Afin de stocker les métadonnées issues de la pipeline d'enrichissement IA (langue, sentiment, routage), la structure de la table `demandes` a été mise à jour. 

#### Exécution de la migration
Pour appliquer la migration manuellement sur votre instance PostgreSQL :
```bash
psql -U <user> -d <database_name> -f docs/migration_enrichment.sql
```
# Dictionnaire des nouvelles colonnes

Toutes les colonnes ajoutées sont optionnelles (NULLABLE) pour préserver l'intégrité des données historiques.
La colonne langue est ajoutée si elle n'existe pas encore

| Colonne | Type | Description | Exemple / Valeurs |
| :--- | :--- | :--- | :--- |
| **langue** | VARCHAR(5) | Code ISO 639-1 de la langue détectée | 'fr', 'en' |
| **langue_confidence** | FLOAT | Score de confiance du modèle de langue | 0.98 (entre 0 et 1) |
| **sentiment** | VARCHAR(10) | Polarité globale du message | 'positif', 'neutre', 'negatif' |
| **sentiment_score** | FLOAT | Score de confiance du modèle de sentiment | 0.85 |
| **enriched_at** | TIMESTAMPTZ | Horodatage précis de l'enrichissement | 2026-05-25 11:30:00+02 |
| **routed_priority** | VARCHAR(20) | File de routage prioritaire attribuée | 'high_intl', 'high_negative', 'normal' |

Un index nommé `idx_demandes_langue` a également été mis en place sur la colonne `langue` pour optimiser les performances des futures requêtes analytiques et de filtrage.

### 3. Instructions de Déploiement Rapide

#### Étape 1 : Préparation de l'environnement
Configurez vos variables d'environnement (ports, identifiants de BDD) en créant votre fichier `.env` à partir du template : `.env.exemple`

#### Étape 2 : Lancement de la stack complète
Déployez l'infrastructure globale d'une seule commande. Les dépendances croisées `depends_on (service_healthy)` garantissent que l'API attend la totale disponibilité de la base et de MLflow avant de s'instancier :
```bash
make up
```

#### Étape 3 : Application de la migration SQL

Exécutez la mise à jour structurelle de la base de données directement au sein du conteneur de base de données :
```bash
make migrate
```

### 4. Enregistrement et Gouvernance des Modèles (MLflow)

Pour figer et versionner nos artefacts IA (Classification historique, Détection de langue FastText, et Analyse de sentiment DistilCamembert), lancez le script d'enregistrement automatique :
```bash
make register
```

#### Ce script réalise les actions suivantes :

*   1. Crée un Run MLflow pour encapsuler chaque modèle.

*   2. Logue les métriques du benchmark (Module 4), les hyperparamètres et un tag contenant le hash SHA-256 unique du jeu de données d'entraînement.

*   3. Enregistre les modèles dans le Model Registry sous les noms respectifs : fastia-classification, fastia-language, et fastia-sentiment.

*   4. Promeut automatiquement chaque version validée vers le stage sémantique Production.

### 5. Validation et Tests d'Intégration

Une suite de tests de bout en bout (tests/test_integration_stack.py) a été mise en place pour certifier la conformité de la stack déployée face aux exigences du CTO.

Pour exécuter les tests d'intégration directement au sein de l'environnement conteneurisé :
```bash
make test
```

#### Scénarios validés par les tests d'intégration :

*   1. GET /health : Vérifie l'état de santé opérationnel de la stack (Code HTTP 200).

*   2. POST /predict (Flux FR) : Valide qu'un texte francophone retourne une réponse enrichie complète contenant tous les nouveaux attributs (langue, sentiment, métadonnées de sanitisation).

*   3. POST /predict (Flux EN) : Valide la règle métier du routeur qui aiguille automatiquement les langues non-francophones vers la file de priorité internationale high_intl.

*   1. POST /predict (Sécurité - Homoglyphes) : Confirme que l'étape d'input sanitisation intercepte les attaques de mimétisme visuel Unicode et lève le compteur homoglyphs_replaced > 0.

*   5. POST /enrich : Valide l'endpoint de service pur isolé, qui calcule la langue et le sentiment sans exécuter la classification métier ni le routage.

*   6. GET /models : Confirme l'interconnexion au registre et la visibilité des modèles actifs en mémoire.

*   7. GET /models/language/metrics : S'assure que l'API restitue correctement les scores d'audit et l'historique du dataset de benchmark.

### 6. Commandes utiles du Makefile

| Commande | Description |
| :--- | :--- |
| `make up` | Instancie le `.env` si manquant, construit les images et lance la stack en arrière-plan. |
| `make down` | Arrête et nettoie l'ensemble des conteneurs de la stack. |
| `make logs` | Affiche les journaux applicatifs (FastAPI, PG, MLflow) en temps réel. |
| `make migrate` | Injecte le script SQL d'enrichissement dans l'instance PostgreSQL active. |
| `make register` | Exécute le script de packaging et pousse les modèles dans le registre MLflow. |
| `make test` | Déclenche la suite complète de tests de bout en bout avec Pytest dans le conteneur api. |
| `make full` | Lance l'intégralité de la pipeline de traitement de données au sein du conteneur applicatif. |