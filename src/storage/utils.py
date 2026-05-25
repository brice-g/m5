import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """
    Crée et retourne une connexion à la base de données PostgreSQL
    en utilisant les variables d'environnement.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT")
        )
        return conn
    except Exception as e:
        print(f"Erreur de connexion à la base de données : {e}")
        raise RuntimeError(f"Erreur connexion DB: {e}")