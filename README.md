# Module 2 - brief 2 FastIA Data Pipeline 

Ce dépôt contient la pipeline d'audit, de nettoyage et d'anonymisation du dataset client de **FastIA**. L'objectif est de transformer un dataset "artisanal" en un actif de données industriel, auditable et conforme au RGPD pour le fine-tuning de modèle.

## Sommaire
1. [Architecture du Projet](#architecture-du-projet)
2. [Installation et Utilisation](#installation-et-utilisation)
3. [Ingestion multi canal](#ingestion-multi-canal)
4. [Commande d'ingestion](#commandes-dingestion)
5. [Pipeline de Traitement](#pipeline-de-traitement)
6. [Résultats de l'Audit (V1 vs V2)](#résultats-de-laudit-v1-vs-v2)
7. [Conformité et Éthique](#conformité-et-éthique)
8. [Stockage des Données](#stockage-des-données)
9. [Comparatif Audit (v1 vs v2)](#comparatif-audit--v1-vs-v2)
10. [Roadmap Data & Prochaines étapes (Spécifications M3)](#roadmap-data--prochaines-étapes-spécifications-m3)

---

## Architecture du Projet

```text
fastia-data-pipeline/
├── data/
│   ├── raw/          # Données brutes (dataset_fastia_module1.jsonl)
│   ├── interim/      # Étapes de nettoyage intermédiaires
│   └── processed/    # Dataset final nettoyé et anonymisé
├── docs/             # Documentation (Datasheet, Cycle de vie, Audit)
├── src/
│   └── pipeline/     # Code source de la pipeline (Load, Clean, Bias, Anonymize, Validate, Run)
    └── storage/      # Gestion SQL (Load, Dump, Schema SQL, Split, Utils) 
├── tests/            # Tests unitaires Pytest
├── docker-compose.yml # Infrastructure reproductible
└── README.md
└── Makefile          # Automatisation des commandes
```

## Installation et Utilisation

Le projet propose désormais deux méthodes d'installation : une via **Makefile** (recommandée pour la rapidité) et une méthode manuelle.

### 1. Prérequis
* **Docker & Docker Compose** (pour la base de données PostgreSQL)
* **Make** (généralement installé par défaut sur Linux/macOS)
* **Python 3.11**
* **Gestionnaire de paquets pip**
* **Environnement virtuel** (fortement recommandé pour isoler les dépendances)

### 2. Installation 

Commencez par cloner le dépôt, puis installez les dépendances nécessaires :

```bash
# Clonage du projet
git clone [https://github.com/brice-g/m2.git](https://github.com/brice-g/m2.git)

# Création et activation de l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate

# Installation des bibliothèques requises
pip install pandas numpy matplotlib seaborn jupyter loguru pytest
```

**Lancement de la pipeline**

Pour transformer le dataset brut en un jeu de données nettoyé et prêt pour l'entraînement, exécutez la commande suivante depuis la racine du projet :

```bash
python -m src.pipeline.run --input data/raw/dataset_fastia_module1.jsonl --output data/processed/dataset_fastia_clean_v1.jsonl
```
Ce script automatise l'ensemble du flux de traitement, génère le fichier JSONL final et produit un fichier de métadonnées (.meta.json) contenant les statistiques de l'exécution.

Le projet utilise maintenant un Makefile pour simplifier l'exécution de la chaîne complète (du brut aux fichiers d'entraînement).
Exécution du flux "Brut → Train/Test"

Le `Makefile` automatise la gestion de l'environnement et de l'infrastructure

```bash
# 1. Installer les dépendances
make install

# 2. Lancer l'infrastructure PostgreSQL (Docker)
make db-up

# 3. Lancer la pipeline complète
make full
```


**Lancement des tests**

le projet utilise Pytest
pour lancer les tests
```bash
python -m pytest
```
## Ingestion Multi-Canal

La pipeline intègre désormais une couche d'intégration unifiée permettant de capturer et centraliser les flux de données provenant de différents canaux de communication (Web, Chat, et Emails).

```plaintext
SOURCES BRUTES               COUCHE D'INGESTION                   BASE DE DONNÉES
+----------------+             +--------------------+              +-----------------+
|  Flux Web      | ----------> |                    |              |                 |
+----------------+             |                    |              |                 |
|  Flux Chat     | ----------> |  integrate_ingest  | -----------> | PostgreSQL (BDS)|
+----------------+             |  (Dédoublonnage &  |              |  (Table unique) |
|  Flux Email    | ----------> |   Cross-canal)     |              |                 |
|  (.mbox, etc.) |             |                    |              |                 |
+----------------+             +--------------------+              +-----------------+
                                         |
                                         v
                               +--------------------+
                               | Rapports de Rejets |
                               |    et d'Erreurs    |
                               +--------------------+
```

## Commandes d'ingestion

Pour importer les données externes de manière unifiée, utilisez la sous-commande ingest en spécifiant la --source (web, chat ou email) et le chemin du fichier avec --input

``` bash
# 1. Ingestion des données issues du canal WEB
python -m src.pipeline.run ingest --source web --input data/raw/formulaires_web_fastia.json

# 2. Ingestion des données issues du canal CHAT
python -m src.pipeline.run ingest --source chat --input data/raw/chat_logs.csv

# 3. Ingestion des données issues du canal EMAIL (ex: fichier Mbox)
python -m src.pipeline.run ingest --source email --input data/raw/emails_fastia.mbox
## Pipeline de Traitement
```

À la fin de chaque exécution, un récapitulatif précis s'affiche dans les logs (Lignes reçues, insérées, doublons internes, doublons cross-canal et rejets).

## Pipeline de Traitement

Le code est modularisé dans le répertoire `src/pipeline/` pour assurer la reproductibilité des traitements et faciliter la maintenance évolutive :

* **Chargement (`load.py`)** : Responsable de la lecture du fichier JSONL initial et de l'aplatissement des dictionnaires imbriqués (extraction des champs `categorie`, `priorite`, et `reponse_suggeree` depuis l'objet `output`).
* **Nettoyage (`clean.py`)** :
    * **Suppression des doublons** : Élimination des doublons exacts et des quasi-doublons via l'utilisation de hash normalisés.
    * **Normalisation textuelle** : Nettoyage des espaces multiples, uniformisation de la casse et des guillemets tout en préservant le texte brut pour référence.
    * **Gestion des anomalies** : Traitement explicite des valeurs manquantes et filtrage des *outliers* de longueur basés sur le z-score ou l'écart interquartile (IQR).
* **Anonymisation (`anonymize.py`)** : Sécurisation des données par la détection et le masquage des informations personnelles (emails, numéros de téléphone, URLs et noms propres) via des expressions régulières et la reconnaissance d'entités nommées (NER).
* **Validation (`validate.py`)** : Contrôle final de conformité garantissant que le schéma est respecté, que les champs obligatoires sont remplis et que les catégories appartiennent à la liste officielle de FastIA.

## Résultats de l'Audit (V1 vs V2)

L'implémentation de la pipeline permet de transformer un jeu de données artisanal en un actif de données structuré et qualitatif. Voici la comparaison entre le dataset brut et le dataset traité :

| Métrique | Dataset Brut (V1) | Dataset Nettoyé (V2) |
| :--- | :--- | :--- |
| **Volume total** | `100%` des données d'origine | `~92%` (après dédoublonnage et filtrage) |
| **Doublons (Exacts & Quasi)** | Présents (non quantifiés) | **0** (supprimés via `drop_duplicates`) |
| **Valeurs manquantes** | Détectées sur `input` et `output` | **0** (imputées ou supprimées via `handle_missing`) |
| **Données Sensibles (PII)** | Exposées (emails, noms, tél) | **Anonymisées** (remplacées par `[NOM]`, `[EMAIL]`) |
| **Conformité Schéma** | Inexistante (format JSON imbriqué) | **Validée** (flat JSONL conforme au schéma cible) |
| **Outliers de longueur** | Présents (bruit technique) | **Identifiés et écartés** (via Z-score/IQR) |
| **Normalisation** | Casse et espaces hétérogènes | **Uniformisée** (standardisation UTF-8) |

> [!NOTE]  
> Les détails spécifiques sur les distributions de catégories et les biais linguistiques identifiés sont disponibles dans le rapport complet : [`docs/audit_v1.md`](docs/audit_v1.md).


## Conformité et Éthique

La gestion et le traitement des données au sein de ce projet sont régis par des principes stricts de responsabilité et de transparence :

* **Respect du RGPD** :
    * **Minimisation des données** : Seules les données strictement nécessaires à l'entraînement du modèle (input/output) sont conservées.
    * **Privacy by Design** : Intégration native d'une étape d'anonymisation dans la pipeline pour protéger l'identité des clients.
    * **Droit à l'oubli** : La structure modulaire permet de supprimer ou de retraiter facilement des entrées spécifiques si nécessaire.
* **Alignement avec l'AI Act** :
    * **Traçabilité** : Documentation complète du cycle de vie de la donnée, de la source brute jusqu'au dataset final.
    * **Transparence** : Utilisation d'une *Datasheet* pour déclarer les limites, les usages recommandés et les biais potentiels du jeu de données.
* **Analyse et Atténuation des Biais** :
    * **Biais de représentation** : Surveillance des déséquilibres entre les catégories pour éviter une dégradation de la performance sur les classes minoritaires.
    * **Biais linguistiques** : Vérification que le modèle ne sur-apprend pas des corrélations basées uniquement sur la longueur des messages ou le registre de langue.
* **Sécurité des données** : Les informations sensibles (PII) identifiées par NER ou Regex sont systématiquement remplacées par des balises génériques (`[NOM]`, `[COORDONNÉES]`) pour préserver le contexte sans exposer les individus.

*Pour plus de détails sur les choix techniques et éthiques, consultez :* [`docs/risques_ethiques.md`](docs/risques_ethiques.md)

## Stockage des Données

**Schéma de la table demandes**

Le choix s'est porté sur PostgreSQL pour garantir la cohérence des données via un typage strict et permettre un versioning efficace des datasets.
Contrairement à un simple stockage fichier, PostgreSQL permet ici d'assurer l'unicité des entrées (via des contraintes ON CONFLICT) et facilite l'extraction de splits stratifiés grâce à des requêtes SQL ciblées par version

| Colonne | Type | Description |
| :--- | :--- | :--- |
| id | SERIAL | Clé primaire unique | 
| input_text | TEXT | Texte nettoyé et anonymisé| 
| categorie | VARCHAR | "Classe (Demande commercial, Information générale, etc.)"| 
| priorite | VARCHAR | haute ou normale |
| dataset_version | VARCHAR | "Identifiant de version (ex: v1.0, v2.0)" |
| source | VARCHAR | original ou synthetic


## Comparatif Audit : v1 vs v2

Ce tableau compare le dataset après nettoyage initial (v1) et après l'étape d'augmentation synthétique et de split (v2).

| Indicateur | v1 (après Nettoyage) | v2 (après Augmentation) |
| :--- | :--- | :--- |
| Nombre d'exemples | 96 | 112 (89 Train / 23 Test) |
| Répartition Catégories | Hétérogène | Stratifiée (équilibrée) |
| Source des données | 100% Originales | ~86% Originales / 14% Synthétiques |
| Format final | JSONL brut | Format Instruct ([INST]...) |

### Analyse des évolutions
**Gain en volume :** L'ajout de 16 exemples synthétiques ciblés (urgences et messages longs) permet de renforcer les classes minoritaires identifiées lors de l'audit v1.

**Robustesse :** Le formatage en "Instruct" dans la v2 prépare directement le modèle aux interactions de type chatbot.

**Fiabilité :** Le processus inclut désormais une revue de qualité manuelle (revue_echantillon.csv) garantissant que l'augmentation LLM ne dégrade pas la pertinence métier.


## Gestion de l'Infrastructure Docker

Le projet utilise Docker Compose pour garantir un environnement de stockage persistant et reproductible pour l'audit.

**Infrastructure Docker** (docker-compose.yml)

Le fichier définit un service de base de données PostgreSQL 15 avec :

* **Persistance :** Utilisation d'un volume postgres_data pour ne pas perdre les données entre les redémarrages.

* **Initialisation :** Montage du volume ./schema.sql vers le point d'entrée Docker pour automatiser la création des tables.

* **Variables d'environnement :** Configuration flexible du nom de la DB et des identifiants (via .env ou valeurs par défaut).

* **Démarrer la DB :** make db-up (Lances un conteneur PostgreSQL fastia_db sur le port 5432).

* **Initialisation :** Au premier lancement, le fichier schema.sql est automatiquement exécuté pour créer la structure des tables.

* **Arrêter la DB :** make db-down.

* **Nettoyage complet :** make clean (Supprime les caches Python et les fichiers de données intermédiaires).

### Roadmap Data & Prochaines étapes (Spécifications M3)

L'évolution de la pipeline vers le module M3 marque la transition d'un traitement purement structurel vers un **enrichissement sémantique avancé** (NLP/LLM) pour la prise de décision métier.

#### 1. Ce qui a été fait (Validé)
* **Preuve de Concept Sémantique (PoC) :** Évaluation hors-ligne de la brique d'enrichissement sémantique positionnée immédiatement en *Post-Cleaning / Pre-Stockage*.
* **Validation des modèles NLP :**
    * Intégration de `FastText` pour la détection de la langue.
    * Intégration du modèle HuggingFace `cmarkea/distilcamembert-base-sentiment` pour la classification fine du mécontentement client (1 à 5 étoiles).
* **Audit Qualitatif des Verbatims :** Validation de la capacité du modèle de sentiment à remonter de vrais signaux critiques.

#### 2. Ce qui reste à faire (Chantiers prioritaires)
* **Migration du Schéma SQL (Alembic) :** Évolution de la base PostgreSQL pour accueillir les dimensions sémantiques. Création et application du script de migration (`migrations/versions/xxxx_add_enrichment_columns.py`) pour ajouter les colonnes :
    * `langue_confidence` (`NUMERIC/FLOAT`)
    * `sentiment` (`VARCHAR(20)`)
    * `sentiment_score` (`NUMERIC/FLOAT`)
* **Généralisation Ciblée de l'Enrichissement :** Implémentation industrielle du composant `enrich_language` et `enrich_sentiment` dans la pipeline globale de production. Conformément aux arbitrages du Comité Produit, l'enrichissement de langue sera restreint aux seuls canaux **Web** (35,71 % hors-FR) et **Chat** (18,18 % hors-FR) pour des raisons d'optimisation des coûts (le canal Email restant à 100 % francophone).
* **Binarisation de la Priorité Métier :** Développement du post-traitement convertissant les prédictions (1 et 2 étoiles) en un flag binaire **Priorité Haute** injecté directement dans le routeur de la pipeline FastIA.
* **Ré-entraînement Éventuel & Fine-Tuning :** Analyse des faux positifs (résolutions en direct par le client au sein du même message) et ajustement des performances sur les classes minoritaires détectées lors du split stratifié.

## Auteur
Brice Gandon