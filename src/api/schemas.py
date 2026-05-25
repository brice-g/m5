from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ==========================================
# REQUÊTES (Inputs)
# ==========================================

class PredictRequest(BaseModel):
    """Payload d'entrée pour la prédiction et l'enrichissement global."""
    body: str = Field(..., min_length=1, max_length=10000, description="Corps du texte de la demande utilisateur brut.")
    canal: str = Field(..., description="Canal de communication d'origine (email, web, chat).")

class EnrichRequest(BaseModel):
    """Payload d'entrée pour l'enrichissement unitaire (Modèles IA uniquement)."""
    text: str = Field(..., min_length=1, max_length=2000, description="Texte à analyser (langue + sentiment) sans routage ni classification.")

# ==========================================
# RÉPONSES (Outputs)
# ==========================================

class PredictResponse(BaseModel):
    """Payload de sortie enrichi pour le point d'entrée historique /predict."""
    categorie: str = Field(..., description="Catégorie métier prédite (M3).")
    priorite: str = Field(..., description="Priorité métier calculée initialement (M3).")
    reponse_suggeree: str = Field(..., description="Modèle de réponse contextuelle suggéré pour l'agent support.")
    
    # Nouveaux champs d'enrichissement IA (Module 4)
    langue: str = Field(..., max_length=5, description="Code ISO 639-1 de la langue détectée par FastText.")
    langue_confidence: float = Field(..., ge=0.0, le=1.0, description="Score de confiance du modèle de langue.")
    sentiment: str = Field(..., description="Classe de sentiment (positif, neutre, negatif) via DistilCamembert.")
    sentiment_score: float = Field(..., ge=0.0, le=1.0, description="Score de confiance associé à l'analyse de sentiment.")
    routed_priority: str = Field(..., description="Niveau de priorité finale calculé par le moteur de routage (high_intl, high_negative, normal).")

class EnrichResponse(BaseModel):
    """Payload de sortie de l'analyse IA isolée (sans logique métier)."""
    langue: str = Field(..., description="Code ISO 639-1 détecté.")
    langue_confidence: float = Field(..., description="Indice de confiance langue.")
    sentiment: str = Field(..., description="Label de sentiment détecté.")
    sentiment_score: float = Field(..., description="Indice de confiance sentiment.")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp UTC de l'inférence.")

class ModelInfo(BaseModel):
    """Représentation structurelle des métadonnées d'un modèle actif."""
    name: str = Field(..., description="Nom technique complet du modèle.")
    version: str = Field(..., description="Numéro de version sémantique (ex: 1.2.0).")
    task: str = Field(..., description="Tâche assignée (language_detection, sentiment_analysis).")
    status: str = Field(..., description="Statut opérationnel du composant (active, degraded, offline).")

class ModelMetricsResponse(BaseModel):
    """Données de performance issues de la dernière phase de benchmark."""
    task: str = Field(..., description="Identifiant de la tâche.")
    metric_name: str = Field(..., description="Nom de la métrique principale (Accuracy, F1-Score).")
    metric_value: float = Field(..., description="Valeur numérique obtenue lors du test.")
    benchmark_date: datetime = Field(..., description="Date à laquelle le protocole a été exécuté.")
    dataset_used: str = Field(..., description="Nom ou référence du jeu d'évaluation utilisé.")