# Importation des fonctions principales pour les rendre accessibles directement via le package
from .load import load_jsonl
from .clean import drop_duplicates, normalise_text, handle_missing, flag_length_outliers, anonymize_pii_regex, anonymize_pii_ner, drop_invalid_rows
from .validate import validate

# Optionnel : définir ce qui est exporté lors d'un "from pipeline import *"
__all__ = [
    "load_jsonl",
    "drop_duplicates",
    "normalise_text",
    "handle_missing",
    "flag_length_outliers",
    "anonymize_pii_regex",
    "anonymize_pii_ner",
    "drop_invalid_rows",
    "validate"
]