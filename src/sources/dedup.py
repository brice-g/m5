import hashlib
import re
from datetime import timedelta
from datetime import datetime
from loguru import logger

def normalize_for_hash(text: str) -> str:
    """
    Nettoie grossièrement le texte pour rendre le calcul d'empreinte sémantique robuste :
    Minuscules, retrait de la ponctuation et fusion des espaces contigus.
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return " ".join(text.split())

def calculate_semantic_hash(body: str) -> str:
    """
    Calcule le hash MD5 unique sur la fenêtre des 300 premiers caractères normalisés.
    """
    cleaned = normalize_for_hash(body)[:300]
    return hashlib.md5(cleaned.encode('utf-8')).hexdigest()

def check_cross_channel_duplicate(conn, current_hash: str, sender: str | None, current_time: datetime) -> str:
    """
    Interroge la base de données pour détecter un doublon cross-canal à +/- 48 heures.
    
    Règles d'arbitrage :
    - Même empreinte sémantique textuelle.
    - Émis par le même émetteur (ou si l'un des émetteurs est non identifié comme le Chat).
    """
    cur = conn.cursor()
    start_window = current_time - timedelta(hours=48)
    
    # Recherche dans la table des demandes sur la fenêtre temporelle optimale
    query = """
        SELECT 1
        FROM demandes
        WHERE received_at >= %s
          AND received_at <= %s
          AND canal_metadata->>'semantic_hash' = %s
          AND (
                sender = %s
                OR sender IS NULL
                OR %s IS NULL
          )
        LIMIT 1
    """
    cur.execute(query, (start_window, current_time, current_hash, sender, sender))
    exists  = cur.fetchone()
    cur.close()
    
    return "cross_channel_duplicate" if exists else "active"