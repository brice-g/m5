FROM python:3.11-slim

# Variables d'environnement pour optimiser Python dans Docker
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Installation des dépendances système nécessaires + curl pour le Healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie et installation des dépendances (Bénéficie du cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code source et des artefacts requis
COPY src/ ./src/
COPY model_final/ ./model_final/
COPY library/ ./library/
COPY docs/ ./docs/
COPY tests/ ./tests/

# Création des dossiers nécessaires (logs et stockage éphémère si besoin)
RUN mkdir -p logs

EXPOSE 8000

# Lancement de l'API avec les workers requis
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]