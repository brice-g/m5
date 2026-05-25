import pandas as pd
import json
from pathlib import Path

def load_jsonl(file_path: str) -> pd.DataFrame:
    """
    Charge le dataset au format JSON Lines et l'aplatit en un DataFrame.
    
    Args:
        file_path (str): Chemin vers le fichier .jsonl
        
    Returns:
        pd.DataFrame: DataFrame contenant les colonnes 'input', 'categorie', 
                     'priorite' et 'reponse_suggeree'.
    """
    path = Path(file_path)
    rows = []
    
    if not path.exists():
        raise FileNotFoundError(f"Le fichier {file_path} est introuvable.")

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Transformation du JSON imbriqué en un format plat
            obj = json.loads(line)
            rows.append({
                "input": obj.get("input", ""),
                "categorie": obj.get("output", {}).get("categorie", ""),
                "priorite": obj.get("output", {}).get("priorite", ""),
                "reponse_suggeree": obj.get("output", {}).get("reponse_suggeree", ""),
            })
            
    return pd.DataFrame(rows)