import pandas as pd
from loguru import logger

from .clean import anonymize_pii_ner, anonymize_pii_regex, anonymize_sender_hash

def anonymize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique les différentes méthodes d'anonymisation sur le DataFrame.
    """
    df = anonymize_pii_regex(df)
    df = anonymize_pii_ner(df)
    df = anonymize_sender_hash(df)
    
    logger.info("Anonymisation terminée.")
    return df