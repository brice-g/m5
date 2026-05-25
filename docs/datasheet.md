# Datasheet : Dataset d’Entraînement FastIA (Support & Requêtes)

Ce document détaille les caractéristiques du dataset de 96 exemples utilisé pour le fine-tuning du modèle de réponse client.
Il intègre désormais les fiches spécifiques par canal d'entrée (Email, Formulaire Web, Chatbot)

---

## 1. Motivation
* **Pourquoi le dataset a-t-il été créé ?** Pour entraîner un modèle de langage à classifier les requêtes clients et à suggérer des réponses adaptées.
* **Pour quelle tâche ?** Classification multi-classe (catégorie), classification binaire (priorité) et génération de texte (réponse suggérée).

## 2. Composition et Fiches Sources
* **Volumétrie :** 96 exemples uniques.
* **Structure des données :** Le dataset contient 4 colonnes principales :

| Champ | Type | Description | Valeurs possibles |
| :--- | :--- | :--- | :--- |
| `input` | String | La requête brute du client | Moyenne de 100 caractères |
| `categorie` | String | Type de demande | Support technique, Information générale, Demande commerciale, Demande de transformation, Réclamation |
| `priorite` | String | Niveau d'urgence | `normale`, `haute` |
| `reponse_suggeree` | String | Proposition de réponse | Moyenne de 158 caractères |

### Fiche Source : Formulaire Web (Données semi-structurées)
* **Description :** Requêtes issues du site institutionnel avec catégories pré-remplies par l'utilisateur.
* **Identification :** L'adresse e-mail de l'émetteur est obligatoirement renseignée dans le champ `sender`.
* **Qualité :** Données plus standardisées, facilitant la classification par le modèle.

### Fiche Source : Chatbot / Chat (Requêtes courtes et directes)
* **Description :** Flux de conversations instantanées, messages généralement plus courts.
* **Particularité (Limite du Chat Anonyme) :** Si un log de chat ne contient pas d'adresse e-mail dans le champ `sender`, l'algorithme refuse la déduplication croisée afin d'éviter d'assimiler par erreur tous les visiteurs anonymes à une seule entité.
* **Impact ML :** Les lignes anonymes restent uniques et isolées pour l'entraînement.

**Distributions clés :**
* **Catégories :** Distribution relativement équilibrée (entre 17 et 22 exemples par classe).
* **Priorités :** Déséquilibre marqué avec 71% de priorité normale (68/96) contre 29% de priorité haute (28/96).
* **Contenu sensible :** L'audit a révélé la présence de **Données Identifiables (PII)** (noms, numéros de téléphone, emails) dans environ 11,5% des lignes (11/96).

## 3. Champs Dérivés (Socle d'Enrichissement Sémantique — Évolution Brief 3)
Dans le cadre du cadrage du nouveau besoin métier du Brief 3, de nouveaux champs dérivés (non présents initialement dans la base brute) ont été caractérisés et validés via une Preuve de Concept (PoC) dans `src/pipeline/enrich.py`. 

Bien que ces champs ne soient pas encore définitivement migrés en base de données SQL (en attente de la migration Alembic au Module 4), ils décrivent la structure enrichie de la donnée en sortie de la pipeline de traitement :

| Champ dérivé | Type | Modèle source | Description | Valeurs possibles |
| :--- | :--- | :--- | :--- | :--- |
| `langue` | String | `langdetect` / `fasttext` | Langue prédominante détectée automatiquement à partir du corps textuel du message (`body`). | `fr`, `en`, `es`, `unknown` |
| `langue_confidence` | Float | `langdetect` / `fasttext` | Score de certitude ou probabilité statistique associée à la langue détectée. | `0.0` à `1.0` (0.0 si inconnu/trop court) |
| `sentiment` | String | `distilcamembert-base-sentiment` | Dimension émotionnelle/sémantique qualifiant le niveau d'insatisfaction de l'utilisateur. | `Mécontent`, `Neutre/Satisfait` |
| `sentiment_score` | Float | `distilcamembert-base-sentiment` | Score de probabilité (confiance) a

## 4. Collecte
* **Comment les données ont-elles été collectées ?** Pas d'information. A voir avec le client.
* **Qui a collecté les données ?** Pas d'information. A voir avec le client.
* **Période de collecte :** Pas d'information. A voir avec le client.
**Canaux de provenance :** Email, Formulaire Web et Chatbot, consolidés via un export CRM client et convertis en JSONL.

## 5. Prétraitements et Déduplication
Une étape de nettoyage et d'alignement automatisée est désormais documentée :
* **Gestion des doublons (Approche non-destructive) :** Les doublons exacts sur le champ `input` sont inexistants (0 détecté). Pour les doublons cross-canal (ex: un email suivi d'un chat 2h après), les lignes sont conservées pour l'analytique métier mais marquées `dedup_status = "cross_channel_duplicate"` afin d'être isolées et d'éviter le surapprentissage du modèle IA.
* **Normalisation sémantique :** Calcul d'un hash MD5 unique (`canal_metadata->>'semantic_hash'`) sur les 300 premiers caractères du texte nettoyé (minuscules, retrait de la ponctuation).

## 6. Usages recommandés et déconseillés

### Usages recommandés
* Exercices de fine-tuning.

### Usages déconseillés
* **Mise en production immédiate :** les données extraites des emails, du chat et du formulaire web n'ont pas de données de priorité ni de catégorie.

## 7. Considérations éthiques
* **Risques identifiés (PII) :** Le dataset contient des informations réelles ou réalistes de clients (ex: Mme Dupont, M. Martin). L'utilisation de ce dataset sans anonymisation préalable présente un risque de fuite de données privées via le modèle entraîné.
* **Biais :** Le modèle pourrait favoriser les catégories "Support technique" et "Information générale" qui sont légèrement plus représentées. Aucun exemple de priorité Haute pour la catégorie "Information générale", pour le modèle une information générale ne pourra jamais avoir de priorité Haute (à confirmer avec le client)
* **Risques liés à l'enrichissement sémantique (Brief 3) :** La détection automatique de la langue induit un risque de corrélation ou de catégorisation indirecte liée à l'origine géographique ou culturelle des utilisateurs (sujet à vigilance au sens de l'AI Act). De même, l'automatisation de la détection de sentiment pour de la sur-priorisation de tickets ne doit pas discriminer ou pénaliser les utilisateurs s'exprimant de manière neutre ou non conventionnelle.

## 8. Maintenance
* **Maintenance :** Dataset évolutif avec l'intégration des briques de déduplication et fiches sources.
* **Signalement d'erreurs :** A la personne qui a réalisée l'exercice.
* **Version :** 1.1.0 (Mise à jour multi-sources & déduplication)