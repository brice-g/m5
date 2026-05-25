# Acquis de fin de Module 2 (M2)

Fil rouge : **FastIA** — industrialisation de la chaîne d'approvisionnement en données du modèle de classification de demandes clients.

À la fin de M2, l'apprenant sait :

---

## Brief 1 — Audit et documentation du dataset

- Charger un dataset JSONL d'instruction et l'aplatir en `DataFrame` Pandas
- Conduire un **audit quantitatif** (distributions catégories/priorités, longueurs, doublons exacts et normalisés, valeurs manquantes, valeurs hors schéma)
- Conduire un **audit qualitatif** (échantillonnage stratifié, relecture des `input` / `categorie` / `priorite` / `reponse_suggeree`, repérage manuel des incohérences)
- Repérer les **données potentiellement sensibles** par regex (email, téléphone, URL, IP) et heuristique de noms propres
- Rédiger une **datasheet** au format *Datasheets for Datasets* (Gebru et al.) : motivation, composition, collecte, prétraitements, usages, considérations éthiques, maintenance
- Documenter le **cycle de vie de la donnée** (chaîne d'approvisionnement, schéma de flux, points de rupture)
- Produire un **diagnostic argumenté** alimentant la feuille de route du Brief 2

## Brief 2 — Pipeline de nettoyage reproductible et détection de biais

- Structurer un **package Python** de pipeline (`src/pipeline/load.py`, `clean.py`, `bias.py`, `validate.py`, `anonymize.py`, `run.py`) avec fonctions pures, paramétrées, testées
- Implémenter les traitements de **data-cleaning** : déduplication exacte + normalisée, normalisation textuelle, gestion des valeurs manquantes, détection d'outliers de longueur, validation de schéma (catégories et priorités fermées)
- Conduire un **audit de biais** structuré : représentation, linguistique, biais de réponse, données sensibles
- Implémenter une étape d'**anonymisation** (regex + NER léger via spaCy) avec choix justifiés (placeholder vs suppression)
- Rédiger une **note réglementaire et éthique** croisant RGPD et AI Act avec les choix de la pipeline
- Versionner un **dataset nettoyé v1** (`data/processed/dataset_fastia_clean_v1.jsonl` + métadonnées : date, hash, stats avant/après)
- Couvrir la pipeline avec **Pytest** (fonctions de cleaning + anonymisation)

## Brief 3 — Augmentation, stockage SQL et préparation de la suite

- Identifier les **catégories sous-représentées** et planifier une stratégie d'augmentation ciblée (`docs/plan_augmentation.md`)
- Implémenter au moins **deux techniques d'augmentation** (paraphrase LLM, gabarit, back-translation, substitution synonymes EDA) avec flag `source` pour traçabilité et revue manuelle d'un échantillon
- Concevoir un **schéma relationnel** PostgreSQL/MySQL anticipant les sources futures du M3 (table `demandes` avec colonnes `canal`, `langue`, `dataset_version`)
- Implémenter `src/storage/load.py` (chargement idempotent JSONL → SQL) et `src/storage/dump.py` (export SQL → JSONL train/test)
- Produire un **split train/test stratifié** sur `categorie` avec seed fixée et export au format prompt M1
- Orchestrer la pipeline complète **brut → nettoyage → augmentation → SQL → split** via `python -m src.pipeline.run --full`
- Comparer les versions **v1 vs v2** du dataset (effectifs, distribution, longueur moyenne, % synthétiques)

---

## Compétences transversales acquises

- **Documentation rigoureuse** d'un actif data (datasheet, lifecycle, audit, plan)
- **Reproductibilité** d'une pipeline data via packaging Python + CLI + tests
- **Détection et atténuation de biais** sur dataset textuel
- **Choix d'architecture de stockage** justifié au regard du cas d'usage et des évolutions anticipées
- **Conformité** RGPD + AI Act intégrée dans les décisions de design (anonymisation, données sensibles, traçabilité)

---

## Entrées pour M3

- Pipeline FastIA complète et testée : `src/pipeline/` + `src/storage/`
- Base **PostgreSQL** (ou MySQL) peuplée avec la table `demandes`, prête à accueillir de nouvelles colonnes et de nouvelles sources
- **Dataset v2** (original + synthétique) versionné dans la base et exporté en `train_v2.jsonl` / `test_v2.jsonl`
- Schéma SQL prévu pour le multi-canal (champ `canal` déjà présent mais non encore exploité)
- Documentation `docs/datasheet.md`, `docs/data_lifecycle.md`, `docs/risques_ethiques.md`, `docs/plan_augmentation.md`
- Tests Pytest existants — base à étendre

C'est sur ce socle que M3 vient **brancher de nouvelles sources** (emails, formulaires web, chat) sur la pipeline existante, anticiper un nouveau besoin métier, et faire évoluer la base sans casser l'existant.
