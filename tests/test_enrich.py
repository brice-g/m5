import pytest
from datetime import datetime
from src.pipeline.enrich import enrich_language, RawDemande

def test_enrich_language_cases():
    # Cas 1 : Français clair
    req_fr = RawDemande(canal="web", external_id="1", received_at=datetime.now(), body="Bonjour, j'ai un problème d'accès à mon compte utilisateur depuis ce matin.")
    res_fr = enrich_language(req_fr)
    assert res_fr["langue"] == "fr"
    assert res_fr["langue_confidence"] > 0.85

    # Cas 2 : Anglais clair
    req_en = RawDemande(canal="chat", external_id="2", received_at=datetime.now(), body="Hello, I cannot download my invoice FA-2026-0312. It gives me a server error.")
    res_en = enrich_language(req_en)
    assert res_en["langue"] == "en"
    assert res_en["langue_confidence"] > 0.85

    # Cas 3 : Espagnol clair
    req_es = RawDemande(canal="web", external_id="3", received_at=datetime.now(), body="Hola, buenas tardes. Mis datos de facturación han desaparecido por completo.")
    res_es = enrich_language(req_es)
    assert res_es["langue"] == "es"
    assert res_es["langue_confidence"] > 0.85

    # Cas 4 : Mix de langues (FR/EN dominant FR)
    req_mix = RawDemande(canal="chat", external_id="4", received_at=datetime.now(), body="Bonjour, urgent please, my system is totally down, à l'aide.")
    res_mix = enrich_language(req_mix)
    assert res_mix["langue"] in ["fr", "en"]
    assert 0.0 <= res_mix["langue_confidence"] <= 1.0

    # Cas 5 : Chaîne vide (Robustesse)
    req_empty = RawDemande(canal="web", external_id="5", received_at=datetime.now(), body="   ")
    res_empty = enrich_language(req_empty)
    assert res_empty["langue"] == "unknown"
    assert res_empty["langue_confidence"] == 0.0
    
    # Cas 6 : Uniquement des chiffres et caractères spéciaux (Protection plantage)
    req_digits = RawDemande(canal="email", external_id="6", received_at=datetime.now(), body="1234567890 +++ ---")
    res_digits = enrich_language(req_digits)
    assert res_digits["langue"] == "unknown"
    assert res_digits["langue_confidence"] == 0.0