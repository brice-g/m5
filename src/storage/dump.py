import json
import psycopg2.extras
from src.storage.utils import get_db_connection

def dump_version_to_jsonl(version, output_path):
    conn = get_db_connection()
    cur = None
    
    if conn is None:
        return

    try:
        # On utilise RealDictCursor pour avoir les noms de colonnes dans le JSON
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("SELECT * FROM demandes WHERE dataset_version = %s", (version,))
        rows = cur.fetchall()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for row in rows:
                if row.get('created_at'):
                    row['created_at'] = row['created_at'].isoformat()
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
            
        print(f"Export de la version {version} terminé.")
        
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    version = 'v1.0'  
    output_path = 'data/exports/dataset_v1_export.jsonl' 
    
    dump_version_to_jsonl(version, output_path)