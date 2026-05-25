import pytest
from fastapi.testclient import TestClient
from main import app # On importe ton instance FastAPI

client = TestClient(app)

VALID_CATEGORIES = [
    "Support technique",
    "Demande commerciale",
    "Demande de transformation",
    "Réclamation",
    "Information générale"
]

def test_health_check():
    """Vérifie que le endpoint health répond correctement."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_predict_success():
    """Vérifie un cas nominal de prédiction."""
    payload = {"text": "Bonjour, j'ai un problème avec mon accès wifi."}
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "categorie" in data
    assert "priorite" in data
    assert "reponse_suggeree" in data
    
    assert data["categorie"] in VALID_CATEGORIES
    assert data["priorite"] in ["normale", "haute"]

def test_predict_empty_input():
    """Vérifie le comportement sur une entrée vide."""
    payload = {"text": ""}
    response = client.post("/predict", json=payload)
    
    # FastAPI/Pydantic ou ton code devrait rejeter ou gérer cela.
    # Ici, on s'attend à ce que le modèle ou l'API lève une erreur si c'est vide.
    assert response.status_code != 200 
    assert "detail" in response.json()

def test_predict_invalid_input_type():
    """Vérifie le comportement sur un type non textuel (ex: nombre)."""
    payload = {"text": 12345} # Pydantic va tenter de convertir ou échouer
    response = client.post("/predict", json=payload)
    
    # Si Pydantic convertit 12345 en "12345", le test pourrait passer (200).
    # Mais si on attend strictement du texte riche, on vérifie la réponse.
    assert response.status_code in [200, 422] # 422 est l'erreur de validation FastAPI