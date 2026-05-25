import json
from pathlib import Path
from typing import Iterator
from datetime import datetime
from pydantic import BaseModel, Field

class RawDemande(BaseModel):
    canal: str
    external_id: str
    received_at: datetime
    sender: str | None = None
    subject: str | None = None
    body: str
    canal_metadata: dict = Field(default_factory=dict)

def load_web_jsonl(path: Path) -> Iterator[RawDemande]:
    """
    Charge les soumissions de formulaires Web à partir d'un fichier JSON Lines (.jsonl).
    - Traite le fichier ligne par ligne pour éviter de saturer la mémoire RAM.
    - Gère le fallback du sujet si absent.
    - Applique le principe de minimisation RGPD en jetant les consentements marketing.
    """
    if not path.exists():
        raise FileNotFoundError(f"Le fichier spécifié n'existe pas : {path}")

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                
                # Extraction sécurisée des données imbriquées
                form_data = data.get("form", {})
                message_body = form_data.get("message", "").strip()
                
                # Règle Métier 1 : Si pas de message, la demande est invalide
                if not message_body:
                    continue
                
                # Règle Métier 2 : Fallback sur le sujet s'il est absent
                subject = form_data.get("subject", "").strip()
                if not subject:
                    # On prend les 60 premiers caractères du message comme sujet de remplacement
                    subject = message_body[:60] + ("..." if len(message_body) > 60 else "")
                
                # Minimisation RGPD 
                # On ne prend QUE les métadonnées utiles à l'IA (biais géographique via l'IP et environnement via User-Agent)
                canal_metadata = {
                    "user_agent": data.get("user_agent"),
                    "ip_country": data.get("ip_country")
                }
                
                # Conversion propre du timestamp ISO (gestion du suffixe 'Z' pour UTC)
                timestamp_str = data.get("submitted_at", "")
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"
                received_at = datetime.fromisoformat(timestamp_str)
                
                yield RawDemande(
                    canal="web",
                    external_id=str(data.get("submission_id")),
                    received_at=received_at,
                    sender=form_data.get("email"),
                    subject=subject,
                    body=message_body,
                    canal_metadata=canal_metadata
                )
            except Exception as e:
                # Permet de ne pas faire planter toute l'ingestion si une seule ligne est corrompue
                print(f"[Erreur] Ligne {line_num} ignorée suite à une anomalie de parsing : {e}")