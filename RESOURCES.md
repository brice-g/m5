# Ressources — Module 5

## Cadre du module

M5 est le passage du dossier de conception (M4) a la production. On implemente les enrichissements, on conteneurise la stack, on met en place le versionnement (modeles + donnees), la livraison continue et le monitoring operationnel.

---

## Documentation technique

### Conteneurisation et deploiement

- [Docker — Dockerfile reference](https://docs.docker.com/engine/reference/builder/)
- [Docker Compose — specification](https://docs.docker.com/compose/compose-file/)
- [Docker — HEALTHCHECK](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Docker Compose — depends_on et conditions](https://docs.docker.com/compose/startup-order/)
- [Docker — multi-stage builds](https://docs.docker.com/build/building/multi-stage/) — reduction de la taille d'image
- [FastAPI — Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) — chargement des modeles au demarrage

### MLflow — registre de modeles et tracking

- [MLflow — Model Registry](https://mlflow.org/docs/latest/model-registry.html) — versionnement et promotion des modeles
- [MLflow — Tracking](https://mlflow.org/docs/latest/tracking.html) — log metriques et artefacts
- [MLflow — Docker deployment](https://mlflow.org/docs/latest/deployment/deploy-model-locally.html)
- [MLflow — Python API (mlflow.pyfunc)](https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html) — chargement de modeles generiques

### DVC — versionnement des donnees

- [DVC — Get Started](https://dvc.org/doc/start)
- [DVC — Data Versioning](https://dvc.org/doc/use-cases/versioning-data-and-models)
- [DVC — Remote Storage](https://dvc.org/doc/user-guide/data-management/remote-storage)
- [DVC — Pipelines (dvc.yaml)](https://dvc.org/doc/user-guide/pipelines) — pipelines reproductibles
- [DVC vs Git LFS — comparaison](https://dvc.org/doc/user-guide/data-management/large-dataset-optimization)

### CI/CD

- [GitHub Actions — Quickstart](https://docs.github.com/en/actions/quickstart)
- [GitHub Actions — Docker build and push](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images)
- [GitHub Actions — Cache](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
- [Ruff — linter Python rapide](https://docs.astral.sh/ruff/) — configuration et regles
- [Pytest — CI integration](https://docs.pytest.org/en/stable/how-to/usage.html)

### Monitoring et observabilite

- [Prometheus — concepts](https://prometheus.io/docs/concepts/data_model/)
- [prometheus-client Python](https://prometheus.github.io/client_python/) — instrumentation applicative
- [Grafana — Getting started](https://grafana.com/docs/grafana/latest/getting-started/)
- [Streamlit — dashboards](https://docs.streamlit.io/) — alternative legere a Grafana
- [PSI — Population Stability Index (theorie)](https://scholarworks.wmich.edu/dissertations/3208/) — mesure de derive
- [Evidently AI — data drift monitoring](https://www.evidentlyai.com/) — alternative open-source

### Outillage existant (rappel)

- [Loguru](https://loguru.readthedocs.io) — logs structures
- [Pytest](https://docs.pytest.org) — tests
- [Pydantic v2](https://docs.pydantic.dev/latest/) — validation de schemas
- [FastAPI](https://fastapi.tiangolo.com/) — API
- [Alembic](https://alembic.sqlalchemy.org/en/latest/) — migrations SQL

---

## Concepts cles

### MLOps — cycle de vie

- [Google — MLOps: Continuous delivery and automation pipelines in ML](https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning) — niveaux de maturite 0, 1, 2
- [Microsoft — MLOps maturity model](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/mlops-maturity-model)
- [Made With ML — MLOps](https://madewithml.com/courses/mlops/) — cours gratuit couvrant le cycle complet

### Data drift et monitoring de modeles

- [Sculley et al. — Hidden Technical Debt in ML Systems (2015)](https://papers.nips.cc/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html) — papier fondateur sur la dette technique en ML
- [Klaise et al. — Monitoring ML Models in Production (2020)](https://arxiv.org/abs/2007.06299) — survey des approches de monitoring

---

## Cadre reglementaire et ethique (rappel)

- **AI Act — exigences pour les systemes a haut risque** : <https://eur-lex.europa.eu/eli/reg/2024/1689/oj> — article 15 (accuracy, robustesse, cybersecurite) et article 72 (surveillance post-marche)
- **RGPD — article 25** : Protection des donnees des la conception et par defaut
- **ISO/IEC 42001:2023** — Systeme de management de l'IA (pertinent pour le monitoring continu)

---

## Donnees et artefacts

Aucun fichier de donnees specifique n'est fourni pour M5. L'apprenant travaille avec :

| Source | Provenance | Utilisation M5 |
|---|---|---|
| Pipeline multi-source M3 | `src/sources/` | Donnees en base PostgreSQL |
| Jeux d'evaluation M4 | `data/eval/` | Benchmark automatise CI |
| Artefacts modeles M4 | `models/` | Enregistrement MLflow |
| Dossier de conception M4 | `docs/` | Implementation des specs |

---

## Outillage

- [Make — Makefile tutorial](https://makefiletutorial.com/) — pour les commandes de gestion de la stack
- [psutil — monitoring systeme Python](https://psutil.readthedocs.io/) — RAM, CPU
- [httpx — HTTP client async](https://www.python-httpx.org/) — tests d'integration
- [CodeCarbon](https://codecarbon.io/) — suivi empreinte carbone (bonus)
