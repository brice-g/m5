# Acquis de fin de Module 3 (M3)

Fil rouge : **FastIA** — extension de la pipeline à des sources hétérogènes (email, web, chat), anticipation d'un besoin métier de détection de langue et de sentiment.

À la fin de M3, l'apprenant sait :

---

## Brief 1 — Ingestion email et évolution de schéma

- Analyser un script legacy Python (collecte mbox → PostgreSQL) et y **identifier les bugs** (encodage en dur, absence d'idempotence, perte de timezone)
- Corriger le script en utilisant `chardet` pour la détection d'encodage, un `ON CONFLICT` pour l'idempotence, et `email.utils.parsedate_to_datetime` pour les dates timezone-aware
- Concevoir et appliquer une **migration Alembic** ajoutant les colonnes nécessaires au multi-source (`canal`, `raw_metadata JSONB`, `ingested_at`)
- Implémenter un **loader email** propre (`src/sources/email_loader.py`) gérant multipart, HTML→texte via BeautifulSoup, encodages exotiques
- **Valider les entrées** avec Pydantic avant insertion en base
- Exécuter et tester la chaîne complète : mbox → loader → validation → base PostgreSQL

## Brief 2 — Sources web et chat, déduplication cross-canal

- Implémenter un **loader JSON Lines** pour les formulaires web (`src/sources/web_loader.py`)
- Implémenter un **loader CSV** pour les transcripts chat (`src/sources/chat_loader.py`) avec regroupement par session
- Identifier et exclure un champ non conforme RGPD (`consent_marketing`) par minimisation
- Concevoir une stratégie de **déduplication cross-canal** (hash normalisé + fenêtre temporelle) détectant les demandes envoyées sur plusieurs canaux
- Produire une **analyse segmentée** par canal (volumétrie, longueur, doublons, catégories) et documenter les biais d'échantillonnage
- Mettre à jour la datasheet Gebru et le cycle de vie pour refléter les 3 canaux

## Brief 3 — Cadrage d'un nouveau besoin métier et PoC d'enrichissement

- **Reformuler un besoin métier** (détection de langue + sentiment) en objectifs opérationnels mesurables
- **Vérifier empiriquement** une hypothèse métier ("1/3 des demandes sont non-FR") sur les données existantes
- Identifier et évaluer des **sources de données externes** (librairies, modèles pré-entraînés, APIs) selon des critères d'accessibilité, qualité, coût, RGPD
- Concevoir un **plan d'évolution de la pipeline** (schéma cible, migration SQL à venir, impact modèle M1, roadmap)
- Implémenter une **preuve de concept** d'enrichissement (fonction pure `enrich_language` ou `enrich_sentiment`) avec CLI et tests Pytest
- Rédiger une **note d'éco-conception** (consommation, filtrage amont, idempotence d'enrichissement)
- Évaluer les **risques éthiques** de la détection automatique (corrélation langue/origine, décision défavorable par sentiment)

---

## Compétences transversales acquises

- **Ingestion multi-source** : adapter les loaders à chaque format (mbox, JSON Lines, CSV) sans casser la structure unifiée
- **Évolution de schéma** maîtrisée : migrations Alembic versionnées et réversibles
- **Déduplication** à l'échelle cross-canal (heuristiques + fenêtrage temporel)
- **Cadrage métier** structuré avant implémentation : reformulation, personas, critères de succès, hypothèses, non-objectifs
- **Évaluation de sources** sur critères opérationnels et légaux
- **Éco-conception** appliquée à un enrichissement par modèle

---

## Entrées pour M4

- Pipeline FastIA fonctionnelle multi-source : `src/sources/` (email, web, chat) + `src/pipeline/` (clean, validate, augment)
- Base PostgreSQL peuplée depuis 3 canaux, avec colonnes `canal`, `raw_metadata`, `ingested_at`
- **PoC d'enrichissement** (`src/pipeline/enrich.py`) : une étape de détection de langue ou de sentiment implémentée et testée
- **Plan d'évolution** documenté : schéma cible avec colonnes `langue`, `langue_confidence`, `sentiment`, `sentiment_score` prêtes à être migrées
- Documentation à jour : `docs/datasheet.md`, `docs/data_lifecycle.md`, `docs/risques_ethiques.md`, `docs/cadrage_besoin_metier.md`, `docs/sources_data_evaluation.md`, `docs/plan_evolution_pipeline.md`
- Tests Pytest couvrant loaders, déduplication et enrichissement

C'est sur ce socle que M4 vient **évaluer rigoureusement** les candidats d'enrichissement (benchmark, robustesse, menaces adversariales) et **concevoir l'architecture cible** intégrant langue, sentiment et routage prioritaire dans la pipeline FastIA.
