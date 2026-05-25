import re
import unicodedata
from pydantic import BaseModel, Field

class SanitizedInput(BaseModel):
    """Conteneur Pydantic pour le texte nettoyé et ses métadonnées de sécurité."""
    text: str = Field(..., description="Le texte nettoyé et normalisé prêt pour l'inférence.")
    original_length: int = Field(..., description="Longueur du texte avant traitement.")
    was_truncated: bool = Field(..., description="Indique si le texte a dépassé la limite et a été tronqué.")
    homoglyphs_detected: bool = Field(..., description="Indique si des substitutions d'homoglyphes ont eu lieu.")
    injection_suspected: bool = Field(..., description="Indique si un pattern d'injection de prompt a été détecté.")

# Table de correspondance pour les homoglyphes cyrilliques courants imitants le latin
HOMOGLYPH_MAP = {
    'а': 'a', 'с': 'c', 'е': 'e', 'о': 'o', 'р': 'p', 'х': 'x', 'у': 'y',
    'А': 'A', 'С': 'C', 'Е': 'E', 'О': 'O', 'Р': 'P', 'Х': 'X', 'У': 'Y'
}

def sanitize(text: str, max_length: int = 2000) -> SanitizedInput:
    """
    Nettoie une entrée utilisateur en amont des modèles d'IA.
    
    - Détection et remplacement des homoglyphes (Cyrillique vers Latin & Normalisation NFKC)
    - Suppression des caractères de contrôle invisibles
    - Troncature sécurisée à une longueur max
    - Détection non-bloquante de patterns d'injections
    """
    if not text:
        return SanitizedInput(
            text="",
            original_length=0,
            was_truncated=False,
            homoglyphs_detected=False,
            injection_suspected=False
        )

    original_length = len(text)
    homoglyphs_detected = False
    
    # 1. Suppression des caractères de contrôle (U+0000 à U+001F) sauf whitespace standard (\n, \r, \t)
    cleaned_text = "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\r\t")

    # 2. Détection avancée et remplacement des homoglyphes
    processed_chars = []
    for ch in cleaned_text:
        # Remplacement direct via notre map d'homoglyphes cyrilliques
        if ch in HOMOGLYPH_MAP:
            processed_chars.append(HOMOGLYPH_MAP[ch])
            homoglyphs_detected = True
            continue
            
        # Détection générique par nom Unicode (ex: si une lettre isolée est "CYRILLIC" ou "GREEK")
        try:
            ch_name = unicodedata.name(ch)
            if "CYRILLIC" in ch_name or "GREEK" in ch_name:
                homoglyphs_detected = True
        except ValueError:
            pass # Caractère sans nom officiel
            
        processed_chars.append(ch)

    # Reconstruction et application de NFKC pour les ligatures/variantes de compatibilité
    intermediary_text = "".join(processed_chars)
    normalized_text = unicodedata.normalize('NFKC', intermediary_text)
    
    if normalized_text != intermediary_text:
        homoglyphs_detected = True

    # 3. Détection de patterns d'injection (Regex insensible à la casse)
    injection_keywords = [
        r"\bignore\b", 
        r"\boublie\b", 
        r"\bsystem prompt\b", 
        r"\binstructions précédentes\b", 
        r"\bact as\b"
    ]
    injection_pattern = re.compile("|".join(injection_keywords), re.IGNORECASE)
    injection_suspected = bool(injection_pattern.search(normalized_text))

    # 4. Troncature à la longueur maximale configurée
    was_truncated = len(normalized_text) > max_length
    final_text = normalized_text[:max_length]

    return SanitizedInput(
        text=final_text,
        original_length=original_length,
        was_truncated=was_truncated,
        homoglyphs_detected=homoglyphs_detected,
        injection_suspected=injection_suspected
    )