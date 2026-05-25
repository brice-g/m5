from pathlib import Path
from typing import Literal, List
from dataclasses import dataclass, field
import pandas as pd
import json
from loguru import logger

from src.storage.utils import get_db_connection
from src.sources.web_loader import load_web_jsonl, RawDemande
from src.sources.chat_loader import load_chat_csv
from src.sources.dedup import calculate_semantic_hash, check_cross_channel_duplicate

from typing import Optional

try:
    from src.pipeline.clean import normalise_text
    from src.pipeline.anonymize import anonymize_data
except ImportError:
    # Fallback pédagogique si la structure de test locale diffère
    def normalise_text(df):
        df['input_raw'] = df['input']
        df['input'] = df['input'].str.lower().str.strip()
        return df
    def anonymize_data(df):
        return df

@dataclass
class ErrorDetail:
    external_id: Optional[str]
    error: str
    payload: Optional[dict] = None

@dataclass
class IngestReport:
    source: str
    received: int = 0
    inserted: int = 0
    deduplicated_internal: int = 0
    deduplicated_cross_channel: int = 0
    rejected: int = 0
    errors: List[ErrorDetail] = field(default_factory=list)

def ingest(source: Literal["email", "web", "chat"], path: Path) -> IngestReport:
    """
    Point d'entrée unique de la pipeline d'ingestion multi-source.
    """
    logger.info(f"Début ingestion source={source}, path={path}")

    report = IngestReport(source=source)
    
    # 1. Dispatching de la source vers le bon loader dédié
    try:
        logger.info(f"{report.received} éléments chargés depuis {source}")
        
        if source == "web":
            loaded_items = list(load_web_jsonl(path))
        elif source == "chat":
            loaded_items = list(load_chat_csv(path))
        elif source == "email":
            # Fallback ou liaison avec votre email_loader du Brief 1
            from src.sources.email_loader import load_mbox
            loaded_items = list(load_mbox(path))
        else:
            raise ValueError(f"Type de source non géré : {source}")
    except Exception as e:
        logger.error(f"Erreur d'exécution du loader : {e}")
        report.errors.append(ErrorDetail(external_id=None, error=f"Erreur d'exécution du loader : {e}"))
        return report

    report.received = len(loaded_items)
    if report.received == 0:
        return report

    # Initialisation de la connexion BDD globale
    try:
        conn = get_db_connection()
        if conn is None:
            raise ValueError("La connexion retournée est vide (None)")
    except Exception as e:
        report.errors.append(ErrorDetail(external_id=None, error=f"Connexion BDD échouée : {e}"))
        report.rejected = report.received
        return report

    # 2. Utilisation de l'écosystème Pandas pour le nettoyage global
    records = []
    for item in loaded_items:
        try:
            records.append({
                "external_id": item.external_id,
                "canal": item.canal,
                "received_at": item.received_at,
                "sender": item.sender,
                "subject": item.subject,
                "input": item.body,  # 'input' sert de clé d'entrée
                "canal_metadata": item.canal_metadata
            })
        except Exception as e:
            logger.warning(f"Item rejeté: {e}")
            report.rejected += 1
            report.errors.append(
                ErrorDetail(
                    external_id=getattr(item, "external_id", None),
                    error=f"Erreur parsing item: {e}",
                    payload=getattr(item, "__dict__", {"raw": str(item)})
                )
            )
            continue
    
    df = pd.DataFrame(records)
    
    # Application des traitements de nettoyage et d'anonymisation
    df = normalise_text(df)
    df = anonymize_data(df)

    # 3. Insertion ligne à ligne avec calcul d'empreinte et déduplication croisée
    cur = conn.cursor()
    for _, row in df.iterrows():
        ext_id = row["external_id"]
        canal = row["canal"]
        rec_at = row["received_at"]
        sender = row["sender"]
        subject = row["subject"]
        input_clean = row["input"]
        input_raw = row.get("input_raw", input_clean)
        meta = row["canal_metadata"] or {}

        # Étape A : Idempotence intra-source (Contrainte de sécurité pour éviter les doublons physiques exacts)
        cur.execute("SELECT id FROM demandes WHERE canal = %s AND external_id = %s", (canal, ext_id))
        if cur.fetchone():
            report.deduplicated_internal += 1
            continue

        # Étape B : Calcul du hash de l'empreinte sémantique
        semantic_hash = calculate_semantic_hash(input_clean)
        meta["semantic_hash"] = semantic_hash

        # Étape C : Déduplication Cross-Canal sur la fenêtre glissante de 48 heures
        dedup_status = check_cross_channel_duplicate(conn, semantic_hash, sender, rec_at)
        
        if dedup_status == "cross_channel_duplicate":
            report.deduplicated_cross_channel += 1
            
        # Étape D : Écriture finale en base de données PostgreSQL
        try:
            cur.execute(
                """
                INSERT INTO demandes 
                    (input_text, input_raw, categorie, priorite, source, canal, dataset_version, received_at, external_id, canal_metadata, sender, dedup_status)
                VALUES 
                    (%s, %s, 'à defnir', 'à definir', %s, %s, 'v2', %s, %s, %s, %s, %s)
                """,
                (input_clean, input_raw, f"ingest_{canal}", canal, rec_at, ext_id, json.dumps(meta), sender, dedup_status)
            )
            report.inserted += 1
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion de l'item {ext_id} : {e}")
            conn.rollback()
            report.rejected += 1
            report.errors.append(ErrorDetail(external_id=ext_id, error=f"Échec insertion id {ext_id} : {e}"))
            continue

    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Ingestion terminée pour source={source}. Report: {report}")
    return report