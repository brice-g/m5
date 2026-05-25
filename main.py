import torch
import json
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from loguru import logger

# --- Configuration Loguru ---
# On configure le logger pour écrire dans la console ET dans le fichier logs/api.log
logger.add(
    "logs/api.log", 
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", 
    rotation="10 MB", 
    retention="80 days" 
)

# --- Configuration ---
MODEL_ID = "meta-llama/Llama-3.2-1B"
TOKENIZER_PATH = "./model_final"
LORA_WEIGHTS_PATH = "./model_final/run2"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

app = FastAPI(title="FastIA API")

# --- Chargement Global (au démarrage) ---
logger.info(f"Démarrage de l'application. Chargement du modèle sur {DEVICE}...")
print(f"Chargement du modèle sur {DEVICE}...")

try:
    # 1. Chargement du Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH)
    tokenizer.pad_token = tokenizer.eos_token

    # 2. Chargement du modèle de base
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        device_map="auto"
    )

    # 3. Chargement de l'adaptateur (LoRA)
    model = PeftModel.from_pretrained(base_model, LORA_WEIGHTS_PATH)
    model.eval()
    
    logger.info("Modèle et adaptateur chargés avec succès.")
    print("Modèle et adaptateur chargés avec succès.")

except Exception as e:
    logger.error(f"Erreur fatale lors du chargement : {str(e)}")
    print(f"Erreur lors du chargement : {str(e)}")
    raise e

# --- Schémas Pydantic ---
class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    categorie: str
    priorite: str
    reponse_suggeree: str

# --- Endpoints ---

@app.get("/health")
def health_check():
    """Vérifie si l'API et le modèle sont opérationnels."""
    logger.info("Endpoint /health appelé")
    return {
        "status": "healthy",
        "device": DEVICE,
        "model_loaded": LORA_WEIGHTS_PATH
    }

@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """Analyse une demande client et retourne un JSON structuré."""
    logger.info("Endpoint /predict appelé")

    start_time = time.time()
    generated_text = ""
    
    # Construction du prompt (identique à ton build_prompt du notebook)
    prompt = (
        f"<s>[INST] Rôle : Tu es un expert en classification de tickets support pour FastIA."
        f"Mission : Analyse la demande utilisateur et renvoie exclusivement un objet JSON."
        f"Contraintes strictes :"
        f"Format : Réponds uniquement en JSON pur, sans texte avant ou après (pas de \"Voici le résultat\")."
        f"Champs obligatoires : categorie, priorite, reponse_suggeree."
        f"Catégories autorisées (Choisir exclusivement parmi) : "
        f"Support technique"
        f"Demande commerciale"
        f"Demande de transformation"
        f"Réclamation"
        f"Information générale"
        f"Priorités autorisées : normale, haute."
        f"Langue : Tout le contenu du JSON doit être en Français.\n\n"
        f"Demande : {request.text} [/INST]"
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)

    try:
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=150,
                temperature=0.1,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Extraction et nettoyage de la réponse
        generated_text = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], 
            skip_special_tokens=True
        ).strip()
        
        # Nettoyage des balises Markdown éventuelles
        clean_json = generated_text.replace("```json", "").replace("```", "").replace("</s>", "").strip()
        
        # Parsing JSON pour s'assurer de la validité avant renvoi
        result = json.loads(clean_json)

        # Calcul du temps de traitement
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Journalisation
        # Format : {time} | {level} | {endpoint} | input={input} | output={output} | duration={duration}ms
        logger.info(
            f"/predict | input={request.text[:50]}... | "
            f"output=cat:{result.get('categorie')}, prio:{result.get('priorite')} | "
            f"duration={duration_ms}ms"
        )
        
        return result

    except json.JSONDecodeError as e:
        logger.warning(f"/predict | JSON invalide généré | input={request.text[:50]}")
        raise HTTPException(status_code=500, detail=f"Le modèle a généré un JSON invalide : {generated_text}")
    except Exception as e:
        logger.exception(f"/predict | Erreur inattendue : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)