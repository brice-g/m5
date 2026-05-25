import argparse
import json
import hashlib
from datetime import datetime
from pathlib import Path
import pandas as pd
from loguru import logger

from .load import load_jsonl

# Import des fonctions de nettoyage
from .clean import (
    drop_duplicates,
    normalise_text,
    handle_missing,
    flag_length_outliers,
    drop_invalid_rows
)
from .anonymize import anonymize_data
from .augment import DataAugmentor
from .validate import validate
from src.storage.dump import dump_version_to_jsonl
from src.storage.split import get_stratified_split, format_dataset, save_metadata, TRAIN_PATH, TEST_PATH, META_PATH
from src.storage.utils import get_db_connection
from psycopg2.extras import execute_values
from src.sources.email_loader import load_mbox

from src.sources.integrate import ingest as integrate_ingest
from typing import Literal, get_args

# --- Configuration des chemins par défaut ---
RAW_DATA = "data/raw/dataset_fastia_module1.jsonl"
PROCESSED_DIR = Path("data/processed")
VERSION = "v1.0"

def compute_hash(file_path):
    """Calcule le hash SHA256 d'un fichier."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_pipeline(input_path: str, output_path: str):
    start_time = datetime.now()
    input_p = Path(input_path)
    output_p = Path(output_path)
    
    # Création du dossier de sortie si inexistant
    output_p.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Démarrage du pipeline. Fichier source : {input_path}")

    # 1. Chargement
    df = pd.read_json(input_path, lines=True)
    initial_stats = {
        "count": len(df),
        "hash_raw": compute_hash(input_path)
    }

    # 2. Enchaînement des étapes
    df = handle_missing(df)
    df = normalise_text(df)
    df = drop_invalid_rows(df)
    df = drop_duplicates(df)
    df = flag_length_outliers(df)
    
    # 3. Anonymisation (Regex + NER)
    df = anonymize_data(df)

    # 4. Sauvegarde du fichier nettoyé
    df.to_json(output_path, orient='records', lines=True, force_ascii=False)
    logger.success(f"Fichier nettoyé sauvegardé : {output_path}")

    # 5. Génération des métadonnées
    meta_path = output_p.with_suffix('.meta.json')
    metadata = {
        "pipeline_execution_date": start_time.isoformat(),
        "input_file": str(input_p.name),
        "output_file": str(output_p.name),
        "parameters": {
            "min_length_threshold": 10,
            "ner_model": "fr_core_news_lg"
        },
        "stats": {
            "rows_before": initial_stats["count"],
            "rows_after": len(df),
            "rows_removed": initial_stats["count"] - len(df),
            "outliers_detected": int(df['is_length_outlier'].sum())
        },
        "hashes": {
            "input_sha256": initial_stats["hash_raw"],
            "output_sha256": compute_hash(output_path)
        }
    }

    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    
    logger.success(f"Métadonnées générées : {meta_path}")

def save_to_sql(df: pd.DataFrame, version: str):
    conn = get_db_connection()
    if not conn:
        logger.error("Connexion DB échouée.")
        return
    
    try:
        cur = conn.cursor()
        
        # Préparation des données à partir du DataFrame
        data = df.to_dict('records')
        
        query = """
        INSERT INTO demandes (
            input_text, input_raw, categorie, priorite, 
            reponse_suggeree, source, canal, langue, dataset_version
        ) VALUES %s
        ON CONFLICT (input_text, dataset_version) DO NOTHING;
        """
        
        values = [
            (
                d.get('input'), 
                d.get('input_raw'), 
                d.get('categorie'),
                d.get('priorite'), 
                d.get('reponse_suggeree'), 
                d.get('source', 'synthetic' if d.get('source') == 'synthetic' else 'original'),
                d.get('canal'), 
                d.get('langue', 'fr'), 
                version
            )
            for d in data
        ]
        
        execute_values(cur, query, values)
        conn.commit()
        logger.success(f"Import SQL terminé (Version {version}) avec execute_values.")
        
    finally:
        if conn: conn.close()

def run_full_pipeline():
    """Orchestration complète de la pipeline."""
    start_time = datetime.now()
    logger.info("Démarrage de la pipeline complète FastIA")

    # 1. CHARGEMENT & NETTOYAGE
    logger.info("--- Étape 1 : Nettoyage ---")
    df = load_jsonl(RAW_DATA)
    df = handle_missing(df)
    df = normalise_text(df)
    df = drop_invalid_rows(df)
    df = drop_duplicates(df)
    df = flag_length_outliers(df)
    df = anonymize_data(df)
    
    # 2. AUGMENTATION (B3)
    logger.info("--- Étape 2 : Augmentation ---")
    augmentor = DataAugmentor()
    df = augmentor.run(df) # Inclut la validation interne et la revue manuelle

    # 3. VALIDATION FINALE
    logger.info("--- Étape 3 : Validation ---")
    df = validate(df)

    # 4. SQL (Insertion)
    logger.info("--- Étape 4 : Insertion SQL ---")
    save_to_sql(df, VERSION)

    # 5. DUMP
    logger.info("--- Étape 5 : Dump SQL vers JSONL ---")
    dump_path = PROCESSED_DIR / f"dataset_dump_{VERSION}.jsonl"
    dump_version_to_jsonl(VERSION, str(dump_path))

    # 6. SPLIT TRAIN/TEST
    logger.info("--- Étape 6 : Split Train/Test ---")
    train_ds, test_ds = get_stratified_split(VERSION)
    
    if train_ds:
        # Metadata
        save_metadata(train_ds, test_ds, VERSION, META_PATH)
        # Formatage & Export
        train_ds = format_dataset(train_ds)
        test_ds = format_dataset(test_ds)
        train_ds.to_json(TRAIN_PATH, orient="records", lines=True, force_ascii=False)
        test_ds.to_json(TEST_PATH, orient="records", lines=True, force_ascii=False)
        
    logger.success(f"Pipeline terminée avec succès en {datetime.now() - start_time}")

# Gestion de l'ingestion des sources
def run_ingestion(source_type: str, input_path: str):
    """Orchestre l'ingestion d'une source brute externe (ex: email)."""
    start_time = datetime.now()
    logger.info(f"Début de l'ingestion de la source : {source_type} ({input_path})")

    # Validation du chemin du fichier
    file_path = Path(input_path)
    if not file_path.exists():
        logger.error(f"Le fichier spécifié est introuvable : {file_path}")
        return
    
    # =========================================================================
    # COUCHE D'INGESTION UNIFIÉE (WEB, CHAT & EMAIL)
    # =========================================================================
    if source_type in ["web", "chat", "email"]: 
        logger.info(f"Délégation de l'ingestion {source_type} à la couche d'intégration unifiée...")
        try:
            # On appelle la fonction unifiée globale
            report = integrate_ingest(source=source_type, path=file_path)
            
            logger.info("=== RÉCAPITULATIF DE L'INGESTION UNIFIÉE ===")
            logger.info(f" Demandes reçues (brutes) : {report.received}")
            logger.info(f" Insérées en Base (bds)   : {report.inserted}")
            logger.info(f" Doublons (interne)      : {report.deduplicated_internal}")
            logger.info(f" Doublons (cross-canal)  : {report.deduplicated_cross_channel}")
            logger.info(f" Lignes rejetées          : {report.rejected}")
            
            if report.errors:
                logger.warning(f"Rencontre de {len(report.errors)} erreur(s) mineure(s) :")
                for err in report.errors[:3]:
                    logger.warning(f"  -> {err}")
                    
            logger.success(f"Opération d'ingestion {source_type} exécutée en {datetime.now() - start_time}")
            return
        except Exception as e:
            logger.exception(f"Erreur critique lors de l'ingestion unifiée {source_type} : {e}")
            return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline FastIA")

    # Utilisation de subparsers pour gérer proprement le nouveau mode 'ingest'
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    parser.add_argument("--full", action="store_true", help="Exécuter toute la pipeline ")
    parser.add_argument("--input", type=str, help="Dataset brut (mode manuel)")
    parser.add_argument("--output", type=str, help="Dataset nettoyé (mode manuel)")
    
    # Nouvelle sous-commande 'ingest'
    ingest_parser = subparsers.add_parser("ingest", help="Ingérer des données externes (Mbox, etc.)")
    ingest_parser.add_argument("--source", type=str, required=True, choices=["email", "web", "chat"], help="Type de source à intégrer")
    ingest_parser.add_argument("--input", type=str, required=True, help="Chemin vers le fichier source (ex: data/raw/emails_fastia.mbox)")

    args = parser.parse_args()
    
    try:
        if args.command == "ingest":
            run_ingestion(source_type=args.source, input_path=args.input)
        elif args.full:
            run_full_pipeline()
        elif args.input and args.output:
            from .run import run_pipeline
            run_pipeline(args.input, args.output)
        else:
            logger.error("Utilisez ingest, --full ou spécifiez --input et --output")
            
    except Exception as e:
        logger.exception(f"Échec du pipeline : {e}")