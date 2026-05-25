import json
from psycopg2.extras import execute_values
from src.storage.utils import get_db_connection # Import de la fonction partagée

def load_jsonl_to_sql(filepath):
    conn = get_db_connection()
    cur = None
    
    if conn is None:
        return

    try:
        cur = conn.cursor()
        with open(filepath, 'r', encoding='utf-8') as f:
            data = [json.loads(line) for line in f]
            
        query = """
        INSERT INTO demandes (
            input_text, input_raw, categorie, priorite, 
            reponse_suggeree, source, canal, langue, dataset_version
        ) VALUES %s
        ON CONFLICT (input_text, dataset_version) DO NOTHING;
        """
        
        values = [
            (
                d.get('input'), d.get('input_raw'), d.get('categorie'),
                d.get('priorite'), d.get('reponse_suggeree'), d.get('source'),
                d.get('canal'), d.get('langue', 'fr'), d.get('dataset_version', 'v1.0')
            )
            for d in data
        ]
        
        execute_values(cur, query, values)
        conn.commit()
        print(f"✅ Import terminé.")
        
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    chemin_fichier = "data/processed/dataset_augmente.jsonl" 
    
    print(f"Démarrage de l'importation depuis {chemin_fichier}...")
    load_jsonl_to_sql(chemin_fichier)