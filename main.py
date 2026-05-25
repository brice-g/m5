import torch
import json
import time
from datetime import datetime, timezone
from typing import List
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from loguru import logger

# Import des schémas Pydantic du M4
from src.api.schemas import (
    PredictRequest, PredictResponse, 
    EnrichRequest, EnrichResponse, 
    ModelInfo, ModelMetricsResponse
)

# Import du composant de désinfection du M4
from src.security.input_sanitizer import sanitize

# Import des composants de production du M5 (Étape 2)
from src.pipeline.enrich_language import LanguageEnricher
from src.pipeline.enrich_sentiment import SentimentEnricher
from src.pipeline.route import route_demand

# --- Configuration Loguru ---
logger.add(
    "logs/api.log", 
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", 
    rotation="10 MB", 
    retention="80 days" 
)

# --- Configuration des Modèles ---
MODEL_ID = "meta-llama/Llama-3.2-1B"
TOKENIZER_PATH = "./model_final"
LORA_WEIGHTS_PATH = "./model_final/run2"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

app = FastAPI(
    title="FastIA Production API",
    description="API enrichie avec classification Llama 3.2, détection de langue, analyse de sentiment et routage dynamique.",
    version="2.0.0"
)

# --- Chargement Global des Modèles (au démarrage) ---
logger.info(f"Démarrage de l'application. Chargement des modèles sur {DEVICE}...")
print(f"Chargement des modèles sur {DEVICE}...")

try:
    # 1. Chargement du Tokenizer Llama
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH)
    tokenizer.pad_token = tokenizer.eos_token

    # 2. Chargement du modèle de base Llama
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        device_map="auto"
    )

    # 3. Chargement de l'adaptateur Lora (Module 3)
    model = PeftModel.from_pretrained(base_model, LORA_WEIGHTS_PATH)
    model.eval()
    logger.info("Modèle Llama-3.2 et adaptateur LoRA chargés avec succès.")

    # 4. Initialisation des enrichisseurs (Module 4 & 5)
    lang_enricher = LanguageEnricher()
    sentiment_enricher = SentimentEnricher()
    logger.info("Enrichisseurs de langue et de sentiment chargés avec succès.")
    print("Tous les modèles ont été chargés avec succès.")

except Exception as e:
    logger.critical(f"Erreur fatale lors du chargement des infrastructures IA : {str(e)}")
    print(f"Erreur fatale lors du chargement : {str(e)}")
    raise e


# =========================================================================
# ENDPOINT Historique : GET /health
# =========================================================================
@app.get("/health", summary="Vérifie si l'API et les modèles sont opérationnels.")
def health_check():
    logger.info("Endpoint /health appelé")
    return {
        "status": "healthy",
        "device": DEVICE,
        "llama_model_loaded": LORA_WEIGHTS_PATH,
        "lang_enricher_loaded": lang_enricher.model is not None,
        "sentiment_enricher_loaded": sentiment_enricher.classifier is not None
    }


# =========================================================================
# ENDPOINT 1 : POST /predict (Version finale combinée et enrichie)
# =========================================================================
@app.post(
    "/predict", 
    response_model=PredictResponse, 
    status_code=status.HTTP_200_OK,
    summary="Analyse, classifie via LLM, enrichit et route une demande entrante."
)
async def predict(request: PredictRequest):
    logger.info(f"Réception d'une demande via le canal: {request.canal}")
    start_time = time.time()
    
    try:
        # 1. Alignement Sécurité : Désinfection immédiate de l'entrée utilisateur
        sanitized = sanitize(request.body, max_length=10000)
        
        # Log discret si une injection est suspectée (pour garder une trace sans casser le schéma)
        if sanitized.injection_suspected or sanitized.homoglyphs_detected:
            logger.warning(
                f"[SECURITY] Texte nettoyé. Injection suspectée: {sanitized.injection_suspected} | "
                f"Homoglyphes détectés: {sanitized.homoglyphs_detected}"
            )
        
        # 2. Enrichissement : Détection de la langue sur le texte sain
        langue, lang_conf = lang_enricher.analyze(sanitized.text)
        
        # 3. Enrichissement : Analyse de sentiment (uniquement si 'fr')
        sentiment, sent_score = sentiment_enricher.analyze(sanitized.text, lang=langue)
        
        # 4. Moteur de Routage Prioritaire
        routing = route_demand(langue=langue, sentiment=sentiment, sentiment_score=sent_score)
        
        # 5. Inférence LLM (Ancienne logique de classification automatisée du Module 3)
        prompt = (
            f"<s>[INST] Rôle : Tu es un expert en classification de tickets support pour FastIA.\n"
            f"Mission : Analyse la demande utilisateur et renvoie exclusivement un objet JSON.\n"
            f"Contraintes strictes :\n"
            f"- Format : Réponds uniquement en JSON pur, sans texte avant ou après (pas de \"Voici le résultat\").\n"
            f"- Champs obligatoires : categorie, priorite, reponse_suggeree.\n"
            f"- Catégories autorisées : Support technique, Demande commerciale, Demande de transformation, Réclamation, Information générale.\n"
            f"- Priorités autorisées : normale, haute.\n"
            f"- Langue : Tout le contenu du JSON doit être en Français.\n\n"
            f"Demande : {sanitized.text} [/INST]"
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=150,
                temperature=0.1,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Extraction et décodage du JSON généré par Llama
        generated_text = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], 
            skip_special_tokens=True
        ).strip()
        
        # Nettoyage des balises Markdown
        clean_json = generated_text.replace("```json", "").replace("```", "").replace("</s>", "").strip()
        
        # Parsing du JSON généré par le LLM pour extraction
        llama_result = json.loads(clean_json)
        
        # 6. Construction de la réponse unifiée validée par le schéma Pydantic
        response_data = PredictResponse(
            categorie=llama_result.get("categorie", "Information générale"),
            priorite=llama_result.get("priorite", "normale"),
            reponse_suggeree=llama_result.get("reponse_suggeree", ""),
            langue=langue or "unknown",
            langue_confidence=lang_conf,
            sentiment=sentiment or "neutre",
            sentiment_score=sent_score,
            routed_priority=routing.priority,
        )

        # Journalisation des performances
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"/predict | input={sanitized.text[:50]}... | "
            f"output=cat:{response_data.categorie}, prio:{response_data.priorite}, routed_prio:{response_data.routed_priority} | "
            f"duration={duration_ms}ms"
        )
        
        return response_data
        
    except json.JSONDecodeError as e:
        logger.warning(f"/predict | JSON invalide généré par Llama | input={request.body[:50]}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Le modèle de classification a généré un format JSON invalide : {generated_text}"
        )
    except Exception as e:
        logger.error(f"Erreur critique lors du traitement /predict: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Composant d'infrastructure ou modèle IA indisponible."
        )


# =========================================================================
# ENDPOINT 2 : POST /enrich (Enrichissement pur isolé)
# =========================================================================
@app.post(
    "/enrich", 
    response_model=EnrichResponse, 
    status_code=status.HTTP_200_OK,
    summary="Enrichissement unitaire par modèles IA (sans routage ni classification)."
)
async def enrich(request: EnrichRequest):
    try:
        # Validation stricte de la longueur (Contrat d'interface du M4)
        if len(request.text) > 2000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le texte transmis dépasse la limite autorisée de 2000 caractères."
            )

        # Désinfection obligatoire en amont
        sanitized = sanitize(request.text, max_length=2000)
        
        # Inférences isolées
        langue, lang_conf = lang_enricher.analyze(sanitized.text)
        sentiment, sent_score = sentiment_enricher.analyze(sanitized.text, lang=langue)
        
        return EnrichResponse(
            langue=langue or "unknown",
            langue_confidence=lang_conf,
            sentiment=sentiment or "neutre",
            sentiment_score=sent_score,
            processed_at=datetime.now(timezone.utc)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'enrichissement unitaire /enrich: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Erreur interne du moteur d'inférence."
        )


# =========================================================================
# ENDPOINT 3 : GET /models (Registre des modèles actifs)
# =========================================================================
@app.get(
    "/models", 
    response_model=List[ModelInfo],
    summary="Liste les métadonnées et états des modèles IA actuellement en mémoire."
)
async def get_active_models():
    models_status = [
        ModelInfo(
            name="meta-llama/Llama-3.2-1B-LoRA",
            version="3.2.0-run2",
            task="text_classification_&_generation",
            status="active" if model else "offline"
        ),
        ModelInfo(
            name="fasttext-language-detector",
            version="1.0.0",
            task="language_detection",
            status="active" if lang_enricher.model else "degraded"
        ),
        ModelInfo(
            name="distilcamembert-sentiment-fr",
            version="2.1.0",
            task="sentiment_analysis",
            status="active" if sentiment_enricher.classifier else "offline"
        )
    ]
    return models_status


# =========================================================================
# ENDPOINT 4 : GET /models/{task}/metrics (Métriques de benchmark d'un modèle)
# =========================================================================
@app.get(
    "/models/{task}/metrics", 
    response_model=ModelMetricsResponse,
    summary="Récupère les scores du dernier protocole d'évaluation pour une tâche donnée."
)
async def get_model_metrics(task: str):
    # Validation du paramètre d'URL (Contrat d'interface)
    if task not in ["language", "sentiment"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tâche invalide. Valeurs autorisées: 'language' ou 'sentiment'."
        )
        
    # Retourne les métriques fixes issues du dernier benchmark validé (M4)
    if task == "language":
        return ModelMetricsResponse(
            task="language",
            metric_name="Accuracy",
            metric_value=0.985,  # Score issu du benchmark M4
            benchmark_date=datetime(2026, 5, 24, 10, 12, tzinfo=timezone.utc),
            dataset_used="langue_eval_200.jsonl"
        )
    else:
        return ModelMetricsResponse(
            task="sentiment",
            metric_name="F1-Score",
            metric_value=0.842,  # Score issu du benchmark M4
            benchmark_date=datetime(2026, 5, 24, 14, 30, tzinfo=timezone.utc),
            dataset_used="sentiment_allocine_test.jsonl"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)