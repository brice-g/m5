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

def get_universal_homoglyph_mapping() -> dict:
    """
    Génère dynamiquement un dictionnaire complet de correspondances pour les homoglyphes
    les plus fréquents (UTS #39) des blocs Cyrillique et Grec imitant le Latin.
    """
    # Table de correspondance universelle (Squelette UTS #39 pour la similarité parfaite)
    raw_pairs = {
        # Cyrillique minuscules et majuscules
        'а': 'a', 'б': '6', 'в': 'b', 'г': 'r', 'д': 'g', 'е': 'e', 'ж': 'zh', 'з': '3',
        'и': 'u', 'й': 'u', 'к': 'k', 'л': 'n', 'м': 'm', 'н': 'h', 'о': 'o', 'п': 'n',
        'р': 'p', 'с': 'c', 'т': 't', 'у': 'y', 'ф': 'o', 'х': 'x', 'ц': 'u', 'ч': 'u',
        'ш': 'w', 'щ': 'w', 'ъ': 'b', 'ы': 'bl', 'ь': 'b', 'э': 'e', 'ю': 'o', 'я': 'r',
        'А': 'A', 'В': 'B', 'Г': 'G', 'Е': 'E', 'З': '3', 'К': 'K', 'М': 'M', 'Н': 'H',
        'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'У': 'Y', 'Х': 'X', 'Ш': 'W',
        # Grec courants
        'α': 'a', 'β': 'b', 'γ': 'y', 'ε': 'e', 'ι': 'i', 'κ': 'k', 'ν': 'v', 'ο': 'o',
        'ρ': 'r', 'τ': 't', 'υ': 'u', 'χ': 'x', 'ω': 'w', 'Α': 'A', 'Β': 'B', 'Ε': 'E',
        'Ζ': 'Z', 'Η': 'H', 'Ι': 'I', 'Κ': 'K', 'Μ': 'M', 'Ν': 'N', 'Ο': 'O', 'Ρ': 'P',
        'Τ': 'T', 'Υ': 'Y', 'Φ': 'F', 'Χ': 'X'
    }
    return raw_pairs

UNIVERSAL_HOMOGLYPH_MAP = get_universal_homoglyph_mapping()

def sanitize(text: str, max_length: int = 2000) -> SanitizedInput:
    """
    Nettoie une entrée utilisateur en amont des modèles d'IA.
    
    - Détection et remplacement universel des homoglyphes (Standard UTS #39 Confusables)
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
    
    # 1. Suppression des caractères de contrôle invisibles (U+0000 à U+001F, U+007F-009F)
    cleaned_chars = []
    for ch in text:
        category = unicodedata.category(ch)
        if category in ("Cc", "Cf") and ch not in "\n\r\t":
            continue
        cleaned_chars.append(ch)
    cleaned_text = "".join(cleaned_chars)

    # 2. Remplacement et Détection Universelle des Homoglyphes
    processed_chars = []
    for ch in cleaned_text:
        # Cas 1 : Le caractère est identifié dans la table universelle des confusables UTS #39
        if ch in UNIVERSAL_HOMOGLYPH_MAP:
            processed_chars.append(UNIVERSAL_HOMOGLYPH_MAP[ch])
            homoglyphs_detected = True
            continue

        try:
            ch_name = unicodedata.name(ch)
        except ValueError:
            processed_chars.append(ch)
            continue

        # Cas 2 : Détection dynamique pour les autres blocs alternatifs (Symboles mathématiques, etc.)
        if any(script in ch_name for script in ["CYRILLIC", "GREEK", "CHEROKEE", "MATHEMATICAL"]):
            homoglyphs_detected = True
            
            # Application de NFKD pour extraire le squelette de compatibilité (ex: symboles mathématiques 𝑩 -> B)
            nfkd_form = unicodedata.normalize('NFKD', ch)
            ascii_equivalent = nfkd_form.encode('ascii', 'ignore').decode('ascii')
            
            if ascii_equivalent:
                processed_chars.append(ascii_equivalent)
            else:
                # Si aucune projection n'est possible, on l'omet pour sécuriser le LLM sans altérer la sémantique
                processed_chars.append("")
        else:
            processed_chars.append(ch)

    # Reconstruction et normalisation finale NFKC pour stabiliser le Tokenizer
    intermediary_text = "".join(processed_chars)
    normalized_text = unicodedata.normalize('NFKC', intermediary_text)
    
    if normalized_text != cleaned_text:
        homoglyphs_detected = True

    # 3. Détection de patterns d'injection de prompt
    injection_keywords = [
        r"\bignore\b", 
        r"\boublie\b", 
        r"\bsystem prompt\b", 
        r"\binstructions précédentes\b", 
        r"\bact as\b"
    ]
    injection_pattern = re.compile("|".join(injection_keywords), re.IGNORECASE)
    injection_suspected = bool(injection_pattern.search(normalized_text))

    # 4. Troncature sécurisée
    was_truncated = len(normalized_text) > max_length
    final_text = normalized_text[:max_length]

    return SanitizedInput(
        text=final_text,
        original_length=original_length,
        was_truncated=was_truncated,
        homoglyphs_detected=homoglyphs_detected,
        injection_suspected=injection_suspected
    )