# Acquis de fin de Module 1 (M1)

Fil rouge : **FastIA** — classification automatique de demandes clients (catégorie, priorité, réponse suggérée) à partir d'un dataset JSONL de 100 exemples.

À la fin de M1, l'apprenant sait :

---

## Brief 1 — Fine-tuning initial & évaluation

- Monter un environnement ML (venv, `transformers`, `peft`, `datasets`, `mlflow`, `accelerate`, `bitsandbytes`) et versionner sur GitHub dès le départ
- **Explorer un dataset d'instruction** (distributions catégories/priorités, équilibre, longueurs)
- Construire un **prompt template d'instruction** (`<s>[INST] ... [/INST] ... </s>`) et splitter 80/20 en respectant la distribution
- **Fine-tuner Llama 3.2 1B avec LoRA/PEFT** (r=8, alpha=16, target `q_proj`/`v_proj`, dropout 0.05) sur hyperparamètres fournis
- Tracker un run dans **MLflow** (paramètres + train/eval loss par époque)
- Évaluer **quantitativement** (courbes de loss, écart train/eval) et **qualitativement** (10 cas couvrant les 5 catégories : validité JSON, cohérence catégorie/priorité/réponse)
- Produire un **diagnostic argumenté** : sous/sur-apprentissage, erreurs systématiques vs aléatoires, actions correctives à envisager

## Brief 2 — Itération & API

- Appliquer ≥1 **action corrective** issue du diagnostic :
  - enrichir le dataset (20–50 exemples ciblés sur catégories faibles)
  - et/ou **ajuster les hyperparamètres** (lr, epochs, dropout LoRA) selon sous/sur-apprentissage
- Lancer un **Run 2** dans MLflow et **comparer Run 1 vs Run 2** (tableau comparatif, courbes, qualité des prédictions)
- Justifier le **choix du meilleur modèle** (pas seulement sur la loss) et le sauvegarder dans `./model_final`
- Exposer le modèle via **FastAPI** :
  - `POST /predict` (entrée `{text}`, sortie `{categorie, priorite, reponse_suggeree}`)
  - `GET /health`
- Valider les entrées avec **Pydantic**, tester les endpoints avec curl/Postman

## Brief 3 — Conteneurisation & mise en production

- Intégrer **Loguru** : logs structurés par endpoint (input, output, durée ms, erreurs) persistés dans `logs/api.log`
- Écrire des **tests Pytest + httpx** :
  - codes HTTP attendus
  - schéma de sortie `/predict`
  - valeurs de `categorie` et `priorite` dans les listes fermées
  - erreurs explicites sur entrées vides ou non textuelles
- Produire un **Dockerfile** propre (image Python slim, `requirements.txt`, port exposé, uvicorn au CMD) + `.dockerignore`
- **Builder et lancer le conteneur**, vérifier les endpoints depuis l'extérieur
- Livrer un **README** complet : architecture, lancement local/Docker, description des endpoints, système de logs, procédure de tests

---

## Compétences transversales acquises

- **Cycle itératif** MLOps : évaluer → comprendre → corriger → réentraîner
- **Traçabilité** des expérimentations via MLflow
- **Reproductibilité** du déploiement via Docker
- **API typée et testée** (FastAPI + Pydantic + Pytest)
- Versionning Git d'un projet IA bout-en-bout (code, dataset, modèle final)

---

## Entrées pour M2

- Dataset `dataset_fastia_module1.jsonl` (éventuellement enrichi au Brief 2)
- API FastIA fonctionnelle, conteneurisée
- Un modèle fine-tuné `./model_final`
- Un historique MLflow (Run 1, Run 2)
- Un README et des briques Docker/Pytest réutilisables

C'est sur ce socle que M2 vient **industrialiser l'amont** : audit, pipeline de nettoyage reproductible, détection de biais, augmentation et migration SQL.
