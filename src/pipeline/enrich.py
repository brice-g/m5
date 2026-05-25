import argparse
import sys
import time
import os
from typing import cast, Any, Dict, Union
import pandas as pd
from pydantic import BaseModel, Field
from datetime import datetime
from langdetect import detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

try:
    import psutil
except ImportError:
    psutil = None

# Fixer le seed pour garantir le déterminisme de langdetect (Heuristique algorithmique)
DetectorFactory.seed = 42

class RawDemande(BaseModel):
    canal: str
    external_id: str
    received_at: datetime
    sender: str | None = None
    subject: str | None = None
    body: str
    canal_metadata: dict = Field(default_factory=dict)

def enrich_language(demande: Union[RawDemande, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Fonction pure d'enrichissement linguistique.
    Prend en entrée une RawDemande ou un dictionnaire, et retourne un dictionnaire 
    enrichi des clés 'langue' et 'langue_confidence' sans effet de bord.
    """
    # Normalisation de l'entrée en dictionnaire
    if isinstance(demande, BaseModel):
        data = demande.model_dump()
    else:
        data = demande.copy()

    # Extraction du texte à analyser (priorité au corps de la demande)
    text_to_analyze = data.get("body", "").strip()

    # Fallback et Robustesse : si texte absent ou trop court pour une détection fiable
    if not text_to_analyze or len(text_to_analyze) < 3:
        data["langue"] = "unknown"
        data["langue_confidence"] = 0.0
        return data

    try:
        # Détection des langues avec probabilités associées
        predictions = detect_langs(text_to_analyze)
        best_prediction = predictions[0]
        
        data["langue"] = str(best_prediction.lang)
        data["langue_confidence"] = float(best_prediction.prob)
        
    except LangDetectException:
        # Gère les cas complexes (uniquement des caractères spéciaux, emojis, ou des URL)
        data["langue"] = "unknown"
        data["langue_confidence"] = 0.0

    return data

def measure_inference_cost(df: pd.DataFrame, text_column: str = "body") -> Dict[str, float]:
    """Mesure précisément le temps d'inférence moyen et l'impact RAM résiduel."""
    process = psutil.Process(os.getpid()) if psutil else None
    
    ram_start = process.memory_info().rss / (1024 * 1024) if process else 0.0
    time_start = time.perf_counter()
    
    # Simulation de passage à l'échelle sur le DataFrame
    for _, row in df.iterrows():
        _ = enrich_language({"body": str(row[text_column])})
        
    time_end = time.perf_counter()
    ram_end = process.memory_info().rss / (1024 * 1024) if process else 0.0
    
    total_time = time_end - time_start
    avg_time_ms = (total_time / len(df)) * 1000 if len(df) > 0 else 0.0
    
    return {
        "total_time_seconds": total_time,
        "avg_time_per_row_ms": avg_time_ms,
        "ram_consumed_mb": max(0.0, ram_end - ram_start)
    }

def main():
    parser = argparse.ArgumentParser(description="CLI d'enrichissement sémantique de la pipeline FastIA.")
    parser.add_argument("--field", choices=["language"], required=True, help="Champ d'enrichissement cible.")
    parser.add_argument("--input", required=True, help="Chemin vers le fichier d'entrée (CSV).")
    parser.add_argument("--output", required=True, help="Chemin vers le fichier de sortie enrichi (CSV).")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Erreur : Le fichier d'entrée '{args.input}' n'existe pas.")
        sys.exit(1)
        
    print(f"Démarrage de l'enrichissement [{args.field}] sur {args.input}...")
    df = pd.read_csv(args.input)
    
    if "body" not in df.columns:
        print("Erreur : La colonne 'body' est requise dans le fichier d'entrée.")
        sys.exit(1)
        
    # Profilage d'Éco-Conception avant écriture finale
    metrics = measure_inference_cost(df, "body")
    
    # Exécution industrielle de la fonction pure
    enriched_records = []
    for _, row in df.iterrows():
        row_dict = cast(dict[str, Any], row.to_dict())
    
        enriched_rec = enrich_language(row_dict)
        enriched_records.append(enriched_rec)
        
    df_enriched = pd.DataFrame(enriched_records)
    df_enriched.to_csv(args.output, index=False)
    
    print(f"Enrichissement terminé ! Fichier sauvegardé dans : {args.output}")
    print(f"\\n--- Rapport d'Inférence d'Éco-Conception ---")
    print(f"Temps moyen par ligne : {metrics['avg_time_per_row_ms']:.2f} ms")
    print(f"Temps total d'exécution : {metrics['total_time_seconds']:.4f} sec")
    print(f"Consommation RAM additionnelle : {metrics['ram_consumed_mb']:.2f} Mo")

if __name__ == "__main__":
    main()