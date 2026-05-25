# Acquis de fin de Module 4 (M4)

Fil rouge : **FastIA** — benchmark rigoureux des modeles candidats, tests adversariaux, et conception d'un dossier d'architecture complet avant implementation.

---

## Synthese des acquis cumules (M0 → M4)

### M0 — Onboarding et integration d'une IA sur etagere

L'apprenant a pris en main l'environnement de travail (Python, venv, Git) et sait :
- Developper une application web integrant un modele IA existant (FastAPI + Streamlit)
- Selectionner et utiliser un modele pre-entraine depuis HuggingFace
- Versionner son code sur GitHub et rediger un README

### M1 — Fine-tuning et exposition d'un modele

L'apprenant a entraine et deploye son premier modele et sait :
- **Fine-tuner un LLM** (Llama 3.2 1B) avec LoRA/PEFT sur le dataset FastIA (100 exemples, 5 categories)
- Mener un **cycle iteratif** : evaluer → diagnostiquer → corriger → reentrainer, avec tracking MLflow
- **Exposer le modele** via FastAPI (`POST /predict`, `GET /health`) avec validation Pydantic
- **Conteneuriser** l'application (Dockerfile, Docker) et ecrire des tests fonctionnels (Pytest + httpx)
- Integrer **Loguru** pour des logs structures persistants

**Artefacts cles** : modele fine-tune `./model_final`, API conteneurisee, historique MLflow (Run 1, Run 2), tests Pytest

### M2 — Pipeline de donnees et qualite

L'apprenant a industrialise la chaine de donnees et sait :
- Conduire un **audit quantitatif et qualitatif** d'un dataset et rediger une **datasheet Gebru**
- Construire un **pipeline de nettoyage reproductible** (package Python : clean, validate, anonymize, bias) avec CLI
- **Detecter et attenues les biais** (representation, linguistique, reponse, donnees sensibles)
- **Anonymiser** les donnees (regex + NER spaCy) en conformite RGPD
- **Augmenter** le dataset sur les categories sous-representees (paraphrase LLM, gabarits, EDA)
- **Migrer les donnees en SQL** (PostgreSQL) avec un schema anticipant le multi-source
- Produire un **split stratifie** reproductible (seed fixee, 80/20)

**Artefacts cles** : `src/pipeline/`, `src/storage/`, base PostgreSQL, dataset v2, `docs/datasheet.md`, `docs/risques_ethiques.md`

### M3 — Ingestion multi-source et cadrage metier

L'apprenant a etendu la pipeline a des sources heterogenes et sait :
- Implementer des **loaders multi-format** (mbox email, JSON web, CSV chat) avec validation Pydantic
- **Corriger un script legacy** (bugs d'encodage, idempotence, timezone)
- Concevoir et appliquer des **migrations Alembic** reversibles pour l'evolution de schema
- Mettre en oeuvre une **deduplication cross-canal** (hash normalise + fenetre temporelle)
- **Cadrer un besoin metier** (detection de langue + sentiment) avec personas, criteres de succes, hypotheses
- Evaluer des **sources de donnees externes** (modeles pre-entraines, APIs) sur criteres operationnels et legaux
- Implementer un **PoC d'enrichissement** (enrich_language ou enrich_sentiment) avec eco-conception

**Artefacts cles** : `src/sources/` (email, web, chat), base PostgreSQL 3 canaux, PoC enrichissement, plan d'evolution, `docs/cadrage_besoin_metier.md`

---

## Acquis specifiques du Module 4

A la fin de M4, l'apprenant sait :

---

## Brief 1 — Benchmark et robustesse

- Constituer un **jeu d'evaluation annote** avec un protocole d'annotation documente (sentiment_eval_50.jsonl)
- Conduire un **benchmark comparatif reproductible** entre modeles candidats (langdetect vs fasttext vs XLM-RoBERTa pour la langue ; distilcamembert vs bert-multilingual pour le sentiment)
- Calculer et comparer les metriques standard : **accuracy, precision/recall/F1 par classe, matrice de confusion, temps d'inference, RAM pic**
- Rediger un **threat model** couvrant 4 familles de menaces (evasion, empoisonnement, injection de prompt, extraction de modele) en referencant MITRE ATLAS et NIST AI 100-2
- Executer des **tests adversariaux pratiques** (homoglyphes, code-switching, ironie, injection) sur les 3 modeles et mesurer un taux de robustesse
- Produire une **matrice de decision ponderee** et formuler une recommandation argumentee avec conditions de remise en question

## Brief 2 — Architecture et dossier de conception

- Concevoir un **diagramme d'architecture cible** (Mermaid) distinguant composants existants et nouveaux, avec flux de donnees et points de fallback
- Implementer un **input sanitizer** (`src/security/input_sanitizer.py`) : normalisation homoglyphes, troncature, detection d'injection, suppression caracteres de controle — avec objet `SanitizedInput` Pydantic et 6+ tests Pytest
- Rediger une **migration SQL** ajoutant les colonnes d'enrichissement (`langue`, `sentiment`, `enriched_at`, `routed_priority`) — toutes nullable pour compatibilite ascendante
- Specifier l'**API enrichie** (endpoints `/predict` enrichi, `/enrich`, `/models`, `/models/{task}/metrics`) avec schemas Pydantic dans `src/api/schemas.py`
- Consolider l'**analyse ethique** : risques lies au profilage par langue, decisions automatisees par sentiment (RGPD art. 22), biais de routage
- Produire un **plan d'attenuation** des menaces avec defense par menace, limites connues et effort d'implementation
- Rediger un **plan de mise en oeuvre phase** (3 phases : langue, sentiment, routage prioritaire) avec prerequis, livrables et criteres d'acceptation
- Rediger une **model card** (format Mitchell et al. 2019) pour le modele de langue retenu

---

## Competences transversales acquises

- **Evaluation rigoureuse** : protocole de benchmark reproductible, metriques standard, comparaison multi-criteres
- **Securite offensive et defensive** : taxonomie de menaces, tests adversariaux, implementation de contre-mesures
- **Conception avant implementation** : architecture documentee, spec API, migration preparee, roadmap phasee
- **Documentation de reference** : model cards, threat model, plan d'attenuation — documents reutilisables par une equipe tierce

---

## Entrees pour M5

- **Dossier de conception complet** : `docs/architecture_cible.md`, `docs/spec_api_enrichie.md`, `docs/plan_mise_en_oeuvre.md`
- **Input sanitizer** implemente et teste : `src/security/input_sanitizer.py` + `tests/test_input_sanitizer.py`
- **Schemas Pydantic** de l'API enrichie : `src/api/schemas.py`
- **Migration SQL** redigee mais **non appliquee** : `docs/migration_enrichment.sql`
- **Modeles retenus** documentes : `docs/matrice_decision.md`, `docs/model_card_langue.md`
- **Plan de securite** : `docs/threat_model.md`, `docs/plan_attenuation.md`
- **Benchmark reproductible** : `notebook_brief1_module4.ipynb`, jeux d'evaluation dans `data/eval/`
- Pipeline FastIA M3 fonctionnelle : API `/predict`, Docker, PostgreSQL, pipeline multi-source, PoC enrichissement

---

## Competences du referentiel couvertes a ce stade (M0 → M4)

| Competence | Intitule | Modules |
|---|---|---|
| **C1** | Identifier un jeu de donnees pour les besoins metiers | M2, M3, M4 |
| **C2** | Identifier les risques ethiques et societaux | M2, M3, M4 |
| **C3** | Preparer les donnees (integrite, pertinence) | M2, M3 |
| **C4** | Choisir un modele IA adapte | M4 |
| **C5** | Entrainer le modele de facon automatique et supervisee | M1 |
| **C6** | Implementer le modele d'IA | M0, M1 |
| C7 | Contribuer a l'architecture cible | *introduit en M4 (conception), a approfondir M7* |
| C8 | Mesurer performance et impacts | *introduit en M4 (benchmark), a approfondir M6* |
| C9 | Amelioration continue | *a aborder en M5-M6* |

---

C'est sur ce socle que M5 vient **deployer en production** la pipeline enrichie, mettre en place le versionnement (modeles + donnees), la livraison continue et le monitoring operationnel — couvrant pleinement **C6** (implementation) et **C9** (amelioration continue).
