# Évaluation des Sources de Données Référentielles et d'Enrichissement

Ce document présente l'évaluation approfondie et qualifiée des sources candidates pour répondre aux nouveaux besoins opérationnels de la pipeline FastIA : la détection automatique de la langue pour le routage international et l'analyse de sentiment pour la priorisation des réclamations urgentes.

## Tableau Comparatif des Solutions Évaluées

| Source | Type | Accessible ? | Qualité | Coût | RGPD | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Détection de langue locale (`langdetect`)** | Librairie Python | Oui, gratuit | Bon FR/EN, moyen ES court | Nul | OK | **Retenir** pour la PoC exploratoire rapide. |
| **Détection de langue par `fasttext` (`lid.176.bin`)** | Modèle binaire (~126 Mo) | Oui, libre | Excellent toutes langues | Nul (offline) | OK | **Retenir comme solution cible** de production (latence ultra-faible). |
| **API Google Cloud Translation (`detectLanguage`)** | API REST Cloud | Oui (compte payant) | Excellent | Facturé / requêtes | Données hors UE | **À éviter** (coûts récurrents + contraintes de conformité RGPD). |
| **Sentiment FR — `cmarkea/distilcamembert-base-sentiment`** | Modèle Hugging Face (~270 Mo) | Oui, libre | Bon, mais entraîné sur reviews ≠ support client | Nul (offline) | OK | **Retenir comme baseline** fonctionnelle immédiate. |
| **Sentiment FR — Fine-tuning interne (200 lignes)** | Dataset métier propriétaire | À constituer | Maximale (adaptée au jargon FastIA) | Temps humain (annotation) | OK | **Proposer en V2** (itération d'optimisation continue). |

---

## Fiches d'Évaluation Détaillées par Solution

### 1. Détection de langue locale (`langdetect`)
* **Existence :** Package disponible sur PyPI ([langdetect](https://pypi.org/project/langdetect/)). Port externe de la bibliothèque originale de détection de langue de Google.
* **Disponibilité :** Licence Apache 2.0. Utilisation illimitée, totalement open-source, sans aucune clé d'API ni système de quotas.
* **Accès et Intégration :** Installation simple via `pip install langdetect` au sein de l'environnement virtuel de FastIA. Intégration directe dans Python. *Attention :* Nécessite l'initialisation d'un seed fixe (`DetectorFactory.seed = 42`) pour stabiliser les prédictions algorithmiques.
* **Contraintes Opérationnelles :**
    * *Latence :* Modérée (~15 à 30 ms par requête). Risque d'engorgement si le volume asynchrone augmente fortement.
    * *RAM :* Très faible empreinte mémoire (< 15 Mo).
    * *Dépendances :* Aucune dépendance réseau, l'inférence se fait à 100 % en local sur CPU.
* **Contraintes Légales :** Conformité RGPD totale. Les données textuelles sensibles ne quittent jamais l'infrastructure ou le conteneur de FastIA.

### 2. Détection de langue par `fasttext` (`lid.176.bin`)
* **Existence :** Modèle pré-entraîné par l'équipe Facebook AI Research (FAIR). Bibliothèque disponible sur PyPI ([fasttext-wheel](https://pypi.org/project/fasttext-wheel/) recommandée pour éviter les problèmes de compilation C++ sous certains environnements). Modèle de référence : [lid.176.bin (126 Mo)](https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin).
* **Disponibilité :** Licence MIT / Creative Commons CC-BY-SA. Gratuit, offline, aucun quota d'utilisation.
* **Accès et Intégration :** Nécessite le téléchargement préalable du fichier de poids du modèle (`lid.176.bin`) et son stockage dans le dossier des assets de la pipeline (`src/pipeline/assets/`). Chargement via `fasttext.load_model()`.
* **Contraintes Opérationnelles :**
    * *Latence :* Ultra-faible (< 1 ms par texte), extrêmement performant grâce à son implémentation native en C++.
    * *RAM :* Nécessite ~130 Mo de RAM résidente en permanence pour maintenir le modèle binaire chargé en mémoire.
    * *Dépendances :* Autonome après le téléchargement initial du fichier binaire.
* **Contraintes Légales :** 100 % conforme RGPD, traitement local et hermétique.

### 3. API Google Cloud Translation (`detectLanguage`)
* **Existence :** Service manager Cloud accessible via l'API REST Google Cloud v2/v3 et via le SDK Python officiel `google-cloud-translate` ([Documentation GCP](https://cloud.google.com/translate/docs/basic/detecting-language)).
* **Disponibilité :** Soumis à l'activation d'un compte Google Cloud Platform (GCP) avec facturation activée. Clé d'API ou compte de service JSON obligatoire. Quotas restrictifs par défaut (ajustables mais plafonnés par minute).
* **Accès et Intégration :** Demande l'installation du package et la configuration de la variable d'environnement `GOOGLE_APPLICATION_CREDENTIALS`. Requiert une ouverture des flux réseau sortants (HTTPS/Port 443) depuis les serveurs de production FastIA.
* **Contraintes Opérationnelles :**
    * *Latence :* Dépendante du réseau internet (généralement entre 80 ms et 250 ms par appel HTTP), ce qui dégrade fortement le débit global de la pipeline.
    * *RAM/CPU :* Nulle sur notre serveur (déportée sur l'infrastructure Google).
    * *Dépendances :* Dépendance réseau critique. Si l'API Google ou la connexion internet tombe, l'enrichissement bloque l'ingestion de la pipeline.
* **Contraintes Légales :** Risque de non-conformité sans signature préalable d'un *Data Processing Addendum (DPA)* spécifique avec Google. Risque de transit et de traitement des données clients (emails, chats) hors de l'Union Européenne (USA). À proscrire au vu de la politique stricte de confidentialité de FastIA.

### 4. Sentiment FR — `cmarkea/distilcamembert-base-sentiment`
* **Existence :** Modèle d'analyse de sentiment francophone hébergé sur le Hugging Face Hub ([cmarkea/distilcamembert-base-sentiment](https://huggingface.co/cmarkea/distilcamembert-base-sentiment)). Développé par l'entité CMarkea sur une architecture DistilCamemBERT.
* **Disponibilité :** Licence MIT. Téléchargement libre et utilisation gratuite via la librairie Python `transformers` de Hugging Face.
* **Accès et Intégration :** Nécessite l'installation de `transformers`, `torch` et `sentencepiece`. Le premier appel télécharge automatiquement le modèle et le tokeniseur dans le cache local de la machine.
* **Contraintes Opérationnelles :**
    * *Latence :* ~30 à 80 ms par message sur CPU classique. Supporte la parallélisation ou l'utilisation de GPU pour descendre sous les 5 ms.
    * *RAM :* Environ 270 Mo de RAM pour les poids du modèle, s'élevant à ~600 Mo lors des phases d'inférence active avec PyTorch.
    * *Limitation Métier :* Le modèle a été entraîné sur des corpus d'avis clients marchands (système de notation de 1 à 5 étoiles). Le jargon purement technique ou B2B du support client FastIA peut générer des approximations (ex: un problème technique critique formulé poliment pourrait être sous-évalué).
* **Contraintes Légales :** Inférence s'effectuant à 100 % en local sur notre infrastructure. Parfaite conformité RGPD.

### 5. Sentiment FR — Fine-tuning interne sur 200 demandes annotées
* **Existence :** Source de données à créer de toutes pièces en interne. Nécessite l'extraction d'un fichier CSV de 200 lignes issues de notre table `public.demandes` et l'utilisation d'un micro-outil d'annotation (ex: Label Studio ou simple tableur partagé).
* **Disponibilité :** Propriété exclusive de FastIA. Pas de coût de licence ni de dépendance tiers.
* **Accès et Intégration :** Une fois annotées par l'équipe métier, ces données servent à entraîner un classifieur local léger (ex: modèle linéaire SVM ou Régression Logistique combiné à une vectorisation TF-IDF via `scikit-learn`).
* **Contraintes Opérationnelles :**
    * *Coût initial :* Nécessite environ 3 heures de travail humain pour labelliser proprement les 200 exemples en classes `Mécontent` / `Neutre`.
    * *Latence :* Exceptionnelle (< 2 ms) si l'on utilise un modèle statistique classique à la place d'un Transformer lourd.
    * *RAM :* Infime (< 10 Mo pour un modèle scikit-learn scellé).
* **Contraintes Légales :** Sécurité maximale. Les données restent confinées au sein de notre périmètre, garantissant le respect total des engagements de confidentialité B2B.