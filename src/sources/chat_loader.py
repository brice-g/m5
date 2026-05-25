import csv
from pathlib import Path
from typing import Iterator
from datetime import datetime
from collections import defaultdict
from loguru import logger
from src.sources.web_loader import RawDemande

def load_chat_csv(path: Path) -> Iterator[RawDemande]:
    """
    Charge et agrège les logs conversationnels du Chat en direct depuis un export CSV.
    - Regroupe les lignes par session_id pour reconstruire l'historique complet.
    - Concatène uniquement les messages 'visitor' dans l'ordre chronologique.
    - Conserve l'intégralité du transcript (visiteur + agent) dans les métadonnées.
    """
    if not path.exists():
        raise FileNotFoundError(f"Le fichier chat CSV est introuvable : {path}")

    # Dictionnaire temporaire pour accumuler les messages par session
    session_buckets = defaultdict(list)
    
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            session_buckets[row["session_id"]].append(row)
            
    # Traitement de chaque session reconstruite
    for session_id, interactions in session_buckets.items():
        # Tri chronologique au cas où l'export CSV contiendrait des lignes désordonnées
        try:
            interactions_sorted = sorted(interactions, key=lambda x: datetime.fromisoformat(x["timestamp"].replace("Z", "+00:00")))
        except Exception as e:
            logger.warning(f"Impossible de trier la session {session_id}, ordre d'origine conservé: {e}")
            interactions_sorted = interactions

        if interactions_sorted:
            last_role = (interactions_sorted[-1].get("role") or "").strip().lower()
            
            if last_role == "visitor":
                logger.info(
                    f"Session Chat {session_id} probablement tronquée "
                    f"(dernier message = visitor, export possiblement incomplet)"
                )
            
        visitor_messages = []
        transcript_complet = []
        first_seen_time = None
        
        for interaction in interactions_sorted:
            role = (interaction.get("role") or "").strip().lower()
            message_text = (interaction.get("message") or "").strip()
            timestamp_raw = interaction.get("timestamp", "")
            
            # Parsing propre de la date de l'interaction
            if timestamp_raw.endswith("Z"):
                timestamp_raw = timestamp_raw[:-1] + "+00:00"
            try:
                ts = datetime.fromisoformat(timestamp_raw)
            except ValueError:
                logger.warning(f"Timestamp invalide dans session {session_id}: {timestamp_raw}")
                continue
                
            if role == "visitor" and first_seen_time is None:
                first_seen_time = ts
                
            # Archivage complet dans le transcript (médonnées)
            transcript_complet.append({
                "timestamp": ts.isoformat(),
                "role": role,
                "message": message_text
            })
            
            # Agrégation exclusive des requêtes du client
            if role == "visitor" and message_text:
                visitor_messages.append(message_text)
                
        # Si une session ne contient aucun message visiteur (ex: abandon immédiat), on rejette
        if not visitor_messages:
            logger.warning(f"Session Chat {session_id} rejetée : aucun message en provenance du visiteur.")
            continue
            
        # Concaténation finale des messages du client séparés par des sauts de lignes
        full_body = "\n".join(visitor_messages)
        
        # Détermination du sujet (60 premiers caractères du tout premier message du visiteur)
        first_msg = visitor_messages[0]
        subject = first_msg[:60] + ("..." if len(first_msg) > 60 else "")
        
        yield RawDemande(
            canal="chat",
            external_id=str(session_id),
            received_at=first_seen_time or datetime.now(),
            sender=None,  # Le chat natif est anonyme (pas d'adresse email initiale)
            subject=subject,
            body=full_body,
            canal_metadata={"transcript_complet": transcript_complet}
        )