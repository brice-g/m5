# Model Card — Composant Détection de Langue FastIA

Ce document suit les spécifications du framework de reporting de Mitchell et al. (2019). Il détaille l'identité, les performances, les limites et le cadre d'utilisation éthique du modèle de langue retenu en production pour la pipeline FastIA.

---

## 1. Model Details (Détails du Modèle)
* **Nom technique** : FastText Language Identification (LID)
* **Fichier d'architecture** : `lid.176.bin` (version compressée optimisée pour la production)
* **Version** : 1.0.0
* **Type de modèle** : Classifieur linéaire basé sur des plongements de mots (*word representations*) et de n-grammes de caractères, couplé à une fonction d'activation Softmax.
* **Auteurs / Développeurs** : Meta AI Research (Facebook Artificial Intelligence Research)
* **Date de publication** : 2016-2017
* **Licence** : CC-BY-NC 4.0 / MIT (Modèle distribué en Open-Source)

---

## 2. Intended Use (Cas d'Usage Prévus)
* **Cas d'usage principal** : Détection unitaire et synchrone de la langue d'expression sur les messages entrants (corps textuels) au sein de la pipeline FastIA.
* **Canaux cibles** : Emails, formulaires Web et flux de messagerie instantanée (Chat).
* **Bénéfice attendu** : Aiguillage immédiat et automatisé des flux internationaux vers les équipes de support multilingues appropriées, et activation conditionnelle de l'analyse de sentiment (uniquement pour le français).

---

## 3. Out-of-Scope Uses (Usages Non Prévus / Interdits)
* **Traduction automatique** : Ce modèle n'est pas un modèle de génération ou de traduction ; il ne doit en aucun cas être utilisé pour reformuler ou traduire du texte.
* **Vérification d'identité** : Interdiction d'utiliser ce modèle pour authentifier l'origine nationale ou la citoyenneté d'un utilisateur.
* **Textes ultra-courts** : Le modèle n'est pas calibré pour classifier de manière fiable des chaînes composées de moins de 3 mots ou de moins de 20 caractères (ex: acronymes, références produits).

---

## 4. Training Data (Données d'Entraînement)
* **Sources de données** : Le modèle original a été pré-entraîné sur un corpus massif et diversifié extrait de **Wikipedia**, de **Tatoeba** et de **Projet Gutenberg**.
* **Volume** : Plusieurs gigaoctets de données textuelles couvrant **176 langues indépendantes**.
* **Caractéristiques** : Données nettoyées de manière standardisée par Meta AI, incluant la tokenisation par sous-mots pour capturer la morphologie des langues complexes.

---

## 5. Evaluation Data (Données d'Évaluation Interne)
* **Jeu de données utilisé** : `langue_eval_200.jsonl` (Brief 1)
* **Composition** : **200 exemples** représentatifs des verbatims clients réels, annotés manuellement de manière stricte par notre équipe IA.
* **Distribution** : Équilibre des classes principales du marché de l'entreprise (Français, Anglais, Espagnol).
* **Limites du jeu d'évaluation** : La taille échantillonnée (200 lignes) est optimale pour un diagnostic agile de surface, mais reste insuffisante pour valider statistiquement la robustesse aux dialectes régionaux rares ou aux argots professionnels très spécifiques.

---

## 6. Metrics (Performances du Benchmark)

Les métriques suivantes ont été enregistrées lors de l'exécution réelle du protocole d'évaluation (Brief 1) de la pipeline FastIA :

### Performance Globale
* **Précision globale (Accuracy)** : **100.0%** (`1.000`) sur le jeu de test de 200 exemples.
* **F1-Score par classe** : `1.00` de manière homogène pour l'ensemble des classes principales testées (FR, EN, ES).

### Métriques Opérationnelles et Éco-Conception
* **Latence moyenne d'inférence** : **0.03 ms / document** (Modèle s'exécutant entièrement en CPU sans besoin de processeur graphique GPU).
* **Empreinte mémoire (RAM)** : **< 1 MB** en exécution isolée, garantissant un impact carbone minimal et une éco-conception logicielle exemplaire.

---

## 7. Ethical Considerations (Considérations Éthiques)
* **Risque de profilage indirect** : La langue étant un proxy direct de l'origine nationale ou culturelle, il existe un risque de traitement inéquitable involontaire (SLA dégradé pour les non-francophones). 
  * *Atténuation* : Conformément à l'**Article 5 de l'AI Act**, le code de langue est utilisé uniquement pour l'aiguillage logistique vers un conseiller humain compétent et ne peut jamais servir de critère d'exclusion métier.
* **Biais linguistiques sur la syntaxe** : Les utilisateurs non natifs écrivant au support avec des fautes de grammaire ou de syntaxe complexes risquent de dégrader la confiance du modèle.
  * *Atténuation* : Intégration d'un seuil de sécurité interdisant toute décision d'aiguillage automatique rigide en cas d'incertitude numérique.

---

## 8. Caveats and Recommendations (Limites et Recommandations)
* **Seuil de confiance minimal (Threshold)** : Il est formellement recommandé d'appliquer un **seuil de confiance de 0.70** sur la probabilité Softmax renvoyée par FastText. En deçà de 0.70, le modèle est considéré comme incertain : le `Fallback Handler` prend le relais, affecte la langue `"fr"` par défaut, et journalise l'anomalie.
* **Conditions de revalidation de l'architecture** : Le modèle FastText devra faire l'objet d'un nouvel audit d'architecture et d'un réentraînement si :
  1. Les messages courts de moins de 20 caractères représentent plus de **25% du flux quotidien** de production.
  2. Le volume global quotidien de l'entreprise dépasse **100 000 demandes / jour** (nécessitant le passage sur l'architecture de cache persistant PostgreSQL validée au Brief 2).
  3. L'entreprise s'ouvre à un nouveau marché international majeur dont la langue n'est pas couverte ou est sous-représentée dans notre jeu de test actuel.