import hashlib
import pandas as pd
from loguru import logger 

SALT = "secret_fastia_salt"  # Grain de sel pour l'anonymisation des senders

def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    suppression des doublons exacts + quasi-doublons via hash normalisé
    """
    initial_len = len(df)
    
    # On crée une clé de dédoublonnement normalisée
    df['temp_key'] = df['input'].str.lower().str.strip()
    
    # Suppression
    df = df.drop_duplicates(subset=['temp_key'], keep='first')
    
    # Nettoyage de la colonne temporaire
    df = df.drop(columns=['temp_key'])
    
    # Un log via Loguru qui compte les lignes entrantes, sortantes et supprimées
    logger.info(f"Suppression des doublons. Lignes entrantes : {initial_len} lignes sortantes : {len(df)} lignes supprimées : {initial_len - len(df)}")
    
    return df

def normalise_text(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalisation de base du texte : strip, collapse espaces multiples, 
    uniformisation des guillemets, passage en minuscules.
    Le texte original est préservé dans 'input_raw'.
    """
    initial_len = len(df)
    
    # 1. Sauvegarde du texte original avant toute modification
    df['input_raw'] = df['input']
    
    # 2. Nettoyage et normalisation
    df['input'] = df['input'].str.strip()
    
    # Collapse espaces multiples
    df['input'] = df['input'].str.replace(r'\s+', ' ', regex=True)
    
    # Uniformisation des guillemets
    df['input'] = df['input'].str.replace(r'[“”]', '"', regex=True)
    
    logger.info(f"Normalisation du texte. Lignes entrantes : {initial_len} lignes sortantes : {len(df)}")
    
    return df

def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Gestion des valeurs manquantes : suppression des lignes où 'input' est vide, 
    imputation de 'reponse_suggeree' si elle existe.
    """
    initial_len = len(df)
    
    # 1. Vérification de la colonne 'input'
    if 'input' in df.columns:
        # Suppression des lignes où 'input' est vide ou ne contient que des espaces
        # On s'assure de traiter les NaN éventuels avant le .str.strip()
        df = df[df['input'].fillna('').str.strip() != ''].copy()
    else:
        logger.warning("La colonne 'input' est absente du dataset !")

    # 2. Imputation de 'reponse_suggeree' SEULEMENT si la colonne existe
    if 'reponse_suggeree' in df.columns:
        df['reponse_suggeree'] = df['reponse_suggeree'].fillna("Aucune réponse suggérée")
    else:
        logger.info("Colonne 'reponse_suggeree' absente : imputation ignorée.")
    
    logger.info(f"Gestion des valeurs manquantes. Lignes entrantes : {initial_len} lignes sortantes : {len(df)} lignes supprimées : {initial_len - len(df)}")
    
    return df

def flag_length_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Détection des outliers de longueur dans la colonne 'input' via IQR, ajout d'une colonne 'is_length_outlier' pour marquer les lignes concernées."""
    # Calcul des longueurs
    df['input_length'] = df['input'].str.len()
    
    # Calcul des quantiles et de l'IQR
    Q1 = df['input_length'].quantile(0.25)
    Q3 = df['input_length'].quantile(0.75)
    IQR = Q3 - Q1
    
    # Définition des seuils pour les outliers
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    # Marquage des outliers
    df['is_length_outlier'] = (df['input_length'] < lower_bound) | (df['input_length'] > upper_bound)
    
    logger.info(f"Détection des outliers de longueur. Lignes entrantes : {len(df)} lignes sortantes : {len(df)} outliers détectés : {df['is_length_outlier'].sum()}")
    
    return df



def anonymize_pii_regex(df: pd.DataFrame) -> pd.DataFrame:
    """
    Masque les données personnelles (Emails Téléphones URLs IPs) identifiées lors de l'audit.
    """
    # DETECTION PAR REGEX
    # Regex pour emails
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    # Regex pour téléphones français simples
    phone_regex = r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}'
    #regex pour url
    url_regex = r'https?://\S+'
    #regex pour ip
    ip_regex = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    
    count_emails = df['input'].str.contains(email_regex).sum()
    count_phones = df['input'].str.contains(phone_regex).sum()
    count_urls = df['input'].str.contains(url_regex).sum()
    count_ips = df['input'].str.contains(ip_regex).sum()

    df['input'] = df['input'].replace(email_regex, '[EMAIL]', regex=True)
    df['input'] = df['input'].replace(phone_regex, '[PHONE]', regex=True)
    df['input'] = df['input'].replace(url_regex, '[URL]', regex=True)
    df['input'] = df['input'].replace(ip_regex, '[IP]', regex=True)

    logger.info(f"Anonymisation : environ {count_emails} emails masqués.")
    logger.info(f"Anonymisation : environ {count_phones} téléphones masqués.")
    logger.info(f"Anonymisation : environ {count_urls} URLs masquées.")
    logger.info(f"Anonymisation : environ {count_ips} adresses IP masquées.")

    return df

    #DETECTION PAR NER
import spacy
import subprocess
import sys

try:
    nlp = spacy.load("fr_core_news_lg")
except OSError:
    logger.info("Le modèle fr_core_news_lg n'est pas installé. Téléchargement du modèle fr_core_news_lg...")
    
    subprocess.run([sys.executable, "-m", "spacy", "download", "fr_core_news_lg"])
    nlp = spacy.load("fr_core_news_lg")
    
    logger.info("Modèle fr_core_news_lg téléchargé et chargé avec succès.")

def anonymize_pii_ner(df: pd.DataFrame) -> pd.DataFrame:
    """
    Masque les données personnelles (Noms) identifiées par NER.
    """
    def mask_ner(text):
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == 'PER':
                text = text.replace(ent.text, f'[NAME]')
        return text

    df['input'] = df['input'].apply(mask_ner)

    logger.info(f"Anonymisation : noms détectés et masqués via NER.")
    return df
   

def drop_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    initial_len = len(df) # Stocke la taille initiale
    df = df[df['input'].str.len() > 10].copy()
    
    logger.info(f"Suppression des lignes invalides. Lignes entrantes : {initial_len} lignes sortantes : {len(df)} lignes supprimées : {initial_len - len(df)}")
    return df

def anonymize_sender_hash(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule une empreinte SHA-256 pseudonymisée et irréversible pour la colonne 'sender'.
    Respecte le RGPD en évitant le stockage en clair des adresses e-mails ou identifiants.
    - Si la colonne 'sender' n'existe pas dans le lot (ex: certains formats), on crée la colonne vide.
    - Utilise une sous-fonction et .apply() pour traiter efficacement chaque ligne du DataFrame.
    """
    if 'sender' not in df.columns:
        logger.warning("La colonne 'sender' est absente du DataFrame. Création d'une colonne 'sender' vide.")
        df['sender'] = None
        return df

    def _hash_value(val):
        if pd.isna(val) or not str(val).strip():
            return None
        
        # Nettoyage de base (minuscules, retrait des espaces superflus)
        clean_val = str(val).strip().lower()
        
        # Calcul du SHA-256 combiné avec le Salt
        hasher = hashlib.sha256()
        hasher.update(f"{clean_val}{SALT}".encode("utf-8"))
        return hasher.hexdigest()

    # Application de la fonction sur toute la colonne et création de la nouvelle colonne
    df['sender'] = df['sender'].apply(_hash_value)
    
    # Sécurité RGPD stricte : une fois le hash calculé, on peut supprimer la colonne 'sender' en clair
    # pour éviter qu'elle ne soit stockée ou logguée par erreur par la suite.
    # df = df.drop(columns=['sender'], errors='ignore')

    logger.info("Anonymisation : Colonne 'sender' anonymisée avec succès.")
    return df