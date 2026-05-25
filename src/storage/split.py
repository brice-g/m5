import os
import json
import hashlib
from datetime import datetime
from collections import Counter

import pandas as pd
from datasets import Dataset, ClassLabel

from src.storage.utils import get_db_connection

# =========================
# CONFIG
# =========================
OUTPUT_DIR = "data/processed"
TRAIN_PATH = os.path.join(OUTPUT_DIR, "train_v2.jsonl")
TEST_PATH = os.path.join(OUTPUT_DIR, "test_v2.jsonl")
META_PATH = os.path.join(OUTPUT_DIR, "dataset_v2.meta.json")

SOURCE_VERSION = "v1.0"
SEED = 42
TEST_SIZE = 0.2
TARGET_VERSION = "v2.0"

# =========================
# DATA LOADING + SPLIT
# =========================
def get_stratified_split(version, seed=42):
    conn = get_db_connection()
    if not conn:
        print("Erreur : Impossible de se connecter à la DB")
        return None, None
    
    try:
        # 1. Charger les données via cursor (compatible psycopg2)
        query = """
            SELECT input_text, categorie 
            FROM demandes 
            WHERE dataset_version = %s
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (version,))
        
        rows = cursor.fetchall()
        
        if not rows:
            print(f"Aucune donnée pour la version {version}")
            return None, None
        
        # Récupérer les noms de colonnes proprement
        colnames = [desc[0] for desc in cursor.description]
        
        # Créer le DataFrame
        df = pd.DataFrame(rows, columns=colnames)

        # 2. Convertir en Dataset Hugging Face
        dataset = Dataset.from_pandas(df)

        # AJOUT IMPORTANT
        from datasets import ClassLabel
        labels = sorted(df["categorie"].unique())
        class_label = ClassLabel(names=labels)
        dataset = dataset.cast_column("categorie", class_label)

        # 3. Split stratifié
        split = dataset.train_test_split(
            test_size=TEST_SIZE,
            stratify_by_column="categorie",
            seed=seed
        )

        train_ds = split["train"]
        test_ds = split["test"]

        print(f"Split terminé pour la version {version} (Seed: {seed})")
        print(f"   - Entraînement : {len(train_ds)} exemples")
        print(f"   - Test          : {len(test_ds)} exemples")
        
        # Vérification stratification
        print("\nDistribution des catégories dans le Test set (%) :")
        test_df = test_ds.to_pandas()
        print(test_df['categorie'].value_counts(normalize=True) * 100)

        return train_ds, test_ds

    finally:
        conn.close()


# =========================
# FORMAT FINE-TUNING
# =========================
def format_example(example):
    return {
        "text": f"<s>[INST] {example['input_text']} [/INST] {example['categorie']} </s>"
    }


def format_dataset(ds):
    ds = ds.map(format_example)

    # garder uniquement "text"
    cols_to_remove = [c for c in ds.column_names if c != "text"]
    ds = ds.remove_columns(cols_to_remove)

    return ds


# =========================
# STATS
# =========================
def get_distribution(ds):
    df = ds.to_pandas()
    dist = df["categorie"].value_counts().to_dict()
    return {str(k): int(v) for k, v in dist.items()}

# =========================
# HASH (stable)
# =========================
def compute_hash(train_ds, test_ds):
    df = pd.concat([train_ds.to_pandas(), test_ds.to_pandas()])
    
    # rendre le hash stable (ordre)
    df = df.sort_values(by=["input_text", "categorie"]).reset_index(drop=True)

    content = df.to_csv(index=False)
    return hashlib.md5(content.encode()).hexdigest()


# =========================
# METADATA
# =========================
def save_metadata(train_ds, test_ds, version, output_path):
    train_dist = get_distribution(train_ds)
    test_dist = get_distribution(test_ds)

    dataset_hash = compute_hash(train_ds, test_ds)

    metadata = {
        "version": version,
        "created_at": datetime.utcnow().isoformat(),
        "hash": dataset_hash,
        "splits": {
            "train": len(train_ds),
            "test": len(test_ds)
        },
        "distribution": {
            "train": train_dist,
            "test": test_dist
        }
    }

    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=4)

    print(f"📦 Metadata sauvegardée → {output_path}")


# =========================
# EXPORT
# =========================
def export_jsonl(train_ds, test_ds):
    train_ds.to_json(TRAIN_PATH, orient="records", lines=True, force_ascii=False)
    test_ds.to_json(TEST_PATH, orient="records", lines=True, force_ascii=False)

    print(f"💾 Train → {TRAIN_PATH}")
    print(f"💾 Test  → {TEST_PATH}")


# =========================
# MAIN PIPELINE
# =========================
def main():
    print(f"Pipeline dataset {SOURCE_VERSION}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Split
    train_ds, test_ds = get_stratified_split(
        SOURCE_VERSION,
        seed=SEED
    )

    # VERIFICATION : Si train_ds est None, on arrête tout
    if train_ds is None:
        print("Abandon : Le split n'a pas pu être généré (vérifiez la DB ou la version).")
        return
    
    # Metadata AVANT transformation
    save_metadata(train_ds, test_ds, TARGET_VERSION, META_PATH)

    # Format fine-tuning
    train_ds = format_dataset(train_ds)
    test_ds = format_dataset(test_ds)

    # Export JSONL
    export_jsonl(train_ds, test_ds)

    print("Pipeline terminé avec succès")


if __name__ == "__main__":
    main()