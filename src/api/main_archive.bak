# src/api/main.py (Extrait de l'initialisation des modèles)
import os
import fasttext
from fastapi import FastAPI
from loguru import logger
from transformers import pipeline
import mlflow
from mlflow.tracking import MlflowClient

app = FastAPI(title="FastIA Resilient Production API")

# Configuration de la liaison MLflow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5001")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Déclaration des variables globales des modèles
classifier_model = None
language_model = None
sentiment_model = None

@app.on_event("startup")
async def load_models_lifespan():
    """
    Événement au démarrage de FastAPI : charge dynamiquement les modèles depuis MLflow
    ou bascule sur les fichiers locaux en cas de panne d'infrastructure.
    """
    global classifier_model, language_model, sentiment_model
    client = MlflowClient()

    # --- 1. CHARGEMENT DU MODÈLE DE LANGUE (FASTTEXT) ---
    try:
        logger.info("Tentative de chargement de 'fastia-language' depuis MLflow...")
        # Récupération des métadonnées de la version en Production
        latest_version = client.get_latest_versions("fastia-language", stages=["Production"])[0]
        # On s'assure que le run_id n'est pas None
        if not latest_version.run_id:
            raise ValueError("Le run_id récupéré depuis MLflow est invalide (None)")
        # Téléchargement local temporaire des artefacts depuis le registre
        download_path = client.download_artifacts(latest_version.run_id, "model")
        
        # Chargement en mémoire
        # Trouver le fichier ftz dans le dossier téléchargé
        ftz_file = [os.path.join(download_path, f) for f in os.listdir(download_path) if f.endswith('.ftz') or f.endswith('.bin')][0]
        language_model = fasttext.load_model(ftz_file)
        logger.success(f"[MLFLOW] Modèle de langue chargé (Version du registre : v{latest_version.version})")
    except Exception as e:
        logger.warning(f"[FALLBACK LOCAL] Échec de connexion MLflow pour la langue ({e}). Chargement local...")
        local_path = "models/lid.176.ftz"
        if os.path.exists(local_path):
            language_model = fasttext.load_model(local_path)
            logger.success("[LOCAL] Modèle de langue chargé depuis l'image Docker.")
        else:
            logger.error("[CRITICAL] Aucun artefact local trouvé pour le modèle de langue.")

    # --- 2. CHARGEMENT DU MODÈLE DE SENTIMENT (TRANSFORMERS) ---
    try:
        logger.info("Tentative de chargement de 'fastia-sentiment' depuis MLflow...")
        latest_version = client.get_latest_versions("fastia-sentiment", stages=["Production"])[0]
        # On s'assure que le run_id n'est pas None
        if not latest_version.run_id:
            raise ValueError("Le run_id récupéré depuis MLflow est invalide (None)")
        download_path = client.download_artifacts(latest_version.run_id, "model")
        
        sentiment_model = pipeline("text-classification", model=download_path, device=-1)
        logger.success(f"[MLFLOW] Modèle de sentiment chargé (Version du registre : v{latest_version.version})")
    except Exception as e:
        logger.warning(f"[FALLBACK LOCAL] Échec de connexion MLflow pour le sentiment ({e}). Chargement local...")
        local_path = "models/tf-allocine" if os.path.exists("models/tf-allocine") else "model_final"
        sentiment_model = pipeline("text-classification", model=local_path, device=-1)
        logger.success(f"[LOCAL] Modèle de sentiment chargé depuis le dossier local : {local_path}")

    # --- 3. CHARGEMENT DU MODÈLE DE CLASSIFICATION HISTORIQUE (M3) ---
    try:
        logger.info("Tentative de chargement de 'fastia-classification' depuis MLflow...")
        latest_version = client.get_latest_versions("fastia-classification", stages=["Production"])[0]
        # On s'assure que le run_id n'est pas None
        if not latest_version.run_id:
            raise ValueError("Le run_id récupéré depuis MLflow est invalide (None)")
        download_path = client.download_artifacts(latest_version.run_id, "model")
        
        classifier_model = pipeline("text-classification", model=download_path, device=-1)
        logger.success(f"[MLFLOW] Modèle de classification chargé (Version du registre : v{latest_version.version})")
    except Exception as e:
        logger.warning(f"[FALLBACK LOCAL] Échec de connexion MLflow pour la classification ({e}). Chargement local...")
        classifier_model = pipeline("text-classification", model="model_final", device=-1)
        logger.success("[LOCAL] Modèle de classification historique M3 chargé depuis 'model_final/'.")