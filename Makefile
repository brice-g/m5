# =========================================================================
# Makefile - FastIA Stack Opérationnelle (Modules 3 & 5)
# =========================================================================

.PHONY: help install clean up down logs migrate test full

# --- AIDE & DIAGNOSTIC ---
help:
	@echo "Commandes de développement local (Héritées M3) :"
	@echo "  make install      : Installe les dépendances locales et SpaCy"
	@echo "  make clean        : Nettoie les fichiers temporaires et les caches"
	@echo " "
	@echo "Commandes de la Stack Production Docker (Module 5) :"
	@echo "  make up           : Crée le .env et lance la stack complète en arrière-plan"
	@echo "  make down         : Arrête tous les conteneurs de la stack"
	@echo "  make logs         : Affiche les journaux applicatifs en continu"
	@echo "  make migrate      : Applique la migration SQL d'enrichissement IA sur la BDD"
	@echo "  make test         : Exécute les tests unitaires/intégration dans le conteneur"
	@echo "  make full         : Lance la pipeline complète au sein du conteneur API"

# --- ENVIRONNEMENT LOCAL (M3) ---
install:
	pip install -r requirements.txt
	python -m spacy download fr_core_news_lg

clean:
	@echo "Nettoyage des fichiers générés..."
	rm -rf data/processed/*.jsonl
	rm -rf data/processed/*.meta.json
	rm -f revue_echantillon.csv
	find . -type d -name "__pycache__" -exec rm -rf {} +

# --- GESTION DE LA STACK DOCKER PROD (M5) ---
up:
	@if [ ! -f .env ]; then \
		echo "Fichier .env manquant. Copie depuis .env.example..."; \
		cp .env.example .env; \
	fi
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	@echo "Exécution de la migration SQL d'enrichissement..."
	docker compose exec -T db psql -U postgres_admin_prod -d fastia_prod -f /app/docs/migration_enrichment.sql

test:
	@echo "Lancement de la suite de tests conteneurisée..."
	docker compose exec api pytest tests/

# Réécriture de 'full' pour cibler l'environnement Docker du M5
full: up
	@echo "Attente de la stack puis exécution de la pipeline complète..."
	docker compose exec api python -m src.pipeline.run --full

register:
	@echo "Enregistrement et promotion des modèles dans le registre MLflow..."
	docker compose exec api python -m scripts.register_models