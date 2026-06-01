import os
import time
import pytest
import requests

# Configuration de l'URL cible de l'API de production
# En environnement conteneurisé, "localhost" ou le nom du conteneur selon l'exécuteur
API_URL = os.getenv("TEST_API_URL", "http://localhost:8000")

@pytest.fixture(scope="module", autouse=True)
def wait_for_api_healthy():
    """
    Fixture garantissant que l'API est entièrement démarrée, connectée à sa BDD
    et à MLflow (état healthcheck OK) avant d'exécuter les tests d'intégration.
    """
    timeout = 30  # maximum 30 secondes d'attente
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{API_URL}/health", timeout=2)
            if response.status_code == 200 and response.json().get("status") == "healthy":
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
        
    pytest.fail(f"L'API sur {API_URL} n'a pas répondu au Healthcheck dans le temps imparti.")

# =========================================================================
# TEST 1 : GET /health — Disponibilité Infrastructure
# =========================================================================
def test_api_health_endpoint():
    response = requests.get(f"{API_URL}/health")
    assert response.status_code == 200
    assert response.json().get("status") == "healthy"

# =========================================================================
# TEST 2 : POST /predict — Validation d'une réponse FR complète
# =========================================================================
def test_predict_french_text_complete_response():
    payload = {
        "body": "Bonjour, l'application crash systématiquement au démarrage depuis ce matin. C'est inadmissible, je suis bloqué !",
        "canal": "chat"
    }
    response = requests.post(f"{API_URL}/predict", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # Validation de la structure historique M3
    assert "categorie" in data
    assert "priorite" in data
    assert "reponse_suggeree" in data
    
    # Validation des nouveaux attributs d'enrichissement IA M4/M5
    assert data["langue"] == "fr"
    assert isinstance(data["langue_confidence"], float)
    assert data["langue_confidence"] >= 0.5
    
    assert data["sentiment"] in ["positif", "neutre", "negatif"]
    assert isinstance(data["sentiment_score"], float)
    
    # Validation de la structure imbriquée de désinfection
    assert "sanitization" in data
    assert "injection_suspected" in data["sanitization"]
    assert "homoglyphs_replaced" in data["sanitization"]

# =========================================================================
# TEST 3 : POST /predict — Routage Prioritaire International (EN)
# =========================================================================
def test_predict_english_text_routes_to_high_intl():
    payload = {
        "body": "Hello, I am unable to log in to my premium workspace. Can you assist me quickly?",
        "canal": "email"
    }
    response = requests.post(f"{API_URL}/predict", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["langue"] == "en"
    # Vérification stricte de la règle métier du Router
    assert data["routed_priority"] == "high_intl"

# =========================================================================
# TEST 4 : POST /predict — Détection de sécurité des homoglyphes
# =========================================================================
def test_predict_homoglyphs_detection_and_replacement():
    # 'а' et 'е' cyrilliques insérés à la place des caractères latins
    payload = {
        "body": "Bonjouг, l'аpplicаtion crаsh", 
        "canal": "web"
    }
    response = requests.post(f"{API_URL}/predict", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    # Le filtre input_sanitizer doit lever un flag positif de traitement
    assert data["sanitization"]["homoglyphs_replaced"] > 0

# =========================================================================
# TEST 5 : POST /enrich — Enrichissement unitaire pur (sans routage)
# =========================================================================
def test_enrich_endpoint_isolated_inference():
    payload = {
        "text": "Je suis extrêmement ravi des nouvelles fonctionnalités de votre plateforme."
    }
    response = requests.post(f"{API_URL}/enrich", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    # L'endpoint de service pur ne doit pas renvoyer de routage ou de classification
    assert "categorie" not in data
    assert "routed_priority" not in data
    
    # Doit contenir uniquement les données d'inférence brute
    assert data["langue"] == "fr"
    assert data["sentiment"] == "positif"
    assert "processed_at" in data

# =========================================================================
# TEST 6 : GET /models — Registre de gouvernance des modèles actifs
# =========================================================================
def test_get_models_list():
    response = requests.get(f"{API_URL}/models")
    assert response.status_code == 200
    
    models = response.json()
    assert isinstance(models, list)
    
    # On valide la présence des signatures de nos modèles clés en mémoire
    tasks_actives = [m["task"] for m in models]
    assert "language_detection" in tasks_actives
    assert "sentiment_analysis" in tasks_actives

# =========================================================================
# TEST 7 : GET /models/{task}/metrics — Diagnostics d'audit du benchmark
# =========================================================================
def test_get_model_benchmark_metrics():
    # Test de la tâche d'identification linguistique
    response = requests.get(f"{API_URL}/models/language/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert data["task"] == "language"
    assert "metric_name" in data
    assert isinstance(data["metric_value"], float)
    assert "benchmark_date" in data
    assert "dataset_used" in data

    # Test de gestion d'erreur : Code 422 attendu si la tâche demandée est hors spécifications
    failed_response = requests.get(f"{API_URL}/models/unknown_task/metrics")
    assert failed_response.status_code == 422