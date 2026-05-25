import pandas as pd
from loguru import logger 

def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Validation du schéma : vérifie que 'categorie' appartient à une liste fermée, que 'priorite' est dans {haute, normale}, et que les champs obligatoires ne sont pas vides. Les lignes invalides sont supprimées."""
    initial_len = len(df)
    
    # Définition des valeurs valides pour les champs catégorie et priorité
    valid_categories = {
        "Support technique",
        "Demande commerciale",
        "Demande de transformation",
        "Réclamation",
        "Information générale"
        }
    
    valid_priorities = {"haute", "normale"}
    
    # Validation du schéma
    df = df[df['categorie'].isin(valid_categories)]
    df = df[df['priorite'].isin(valid_priorities)]
    
    logger.info(f"Validation du schéma. Lignes entrantes : {initial_len} lignes sortantes : {len(df)} lignes invalides : {initial_len - len(df)}")
    
    return df