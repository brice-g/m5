.PHONY: help install db-up db-down clean full

help:
	@echo "Commandes disponibles :"
	@echo "  make install      : Installe les dépendances et SpaCy"
	@echo "  make db-up        : Lance la base de données PostgreSQL via Docker"
	@echo "  make db-down      : Arrête le conteneur Docker"
	@echo "  make clean        : Nettoie les fichiers temporaires et caches"
	@echo "  make full         : Lance la pipeline complète (lance Docker automatiquement)"

install:
	pip install -r requirements.txt
	python -m spacy download fr_core_news_lg

db-up:
	@echo "Lancement de la base de données..."
	docker-compose up -d
	@echo "Attente du démarrage de PostgreSQL (5s)..."
	@sleep 5

db-down:
	docker-compose down

clean:
	@echo "Nettoyage des fichiers générés..."
	rm -rf data/processed/*.jsonl
	rm -rf data/processed/*.meta.json
	rm -f revue_echantillon.csv
	find . -type d -name "__pycache__" -exec rm -rf {} +

full: db-up
	@echo "Exécution de la pipeline..."
	python -m src.pipeline.run --full