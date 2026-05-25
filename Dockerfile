FROM python:3.11-slim

# Installation des dépendances système nécessaires pour certains packages Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Définition du dossier de travail
WORKDIR /app

# Copie et installation des dépendances en premier pour profiter du cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du code de l'application
# Cela inclut main.py et tes dossiers de modèle (model_final/)
COPY main.py .
COPY model_final/ ./model_final/

# Création du dossier de logs pour que Loguru puisse écrire dedans
RUN mkdir -p logs

# Exposition du port utilisé par FastAPI
EXPOSE 8000

# Commande de lancement
# --workers 1 est souvent recommandé pour les APIs avec LLM pour éviter de saturer la RAM/VRAM
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]