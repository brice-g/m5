from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger

class RoutingDecision(BaseModel):
    priority: str = Field(..., description="Valeurs possibles: high_intl, high_negative, normal")
    justification: str = Field(..., description="Raison ayant mené à cette règle de routage")

def route_demand(langue: Optional[str], sentiment: Optional[str], sentiment_score: float) -> RoutingDecision:
    """
    Applique les règles de routage prioritaires validées par l'architecture.
    """
    # Règle 1 : Client non francophone -> Priorité Internationale
    if langue is not None and langue != 'fr':
        decision = RoutingDecision(
            priority="high_intl",
            justification=f"Demande détectée en langue étrangère ('{langue}')."
        )
    
    # Règle 2 : Client très insatisfait en FR -> Priorité Négative Urgente
    elif sentiment == "negatif" and sentiment_score > 0.8:
        decision = RoutingDecision(
            priority="high_negative",
            justification=f"Sentiment fortement négatif détecté avec un score de {sentiment_score:.2f}."
        )
    
    # Règle par défaut
    else:
        decision = RoutingDecision(
            priority="normal",
            justification="La demande ne valide aucun critère de sur-priorisation."
        )

    logger.debug(f"[ROUTING] Décision prise: {decision.priority} | Motif: {decision.justification}")
    return decision