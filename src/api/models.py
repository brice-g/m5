from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Demande(Base):
    __tablename__ = 'demandes'

    # Clé primaire obligatoire pour SQLAlchemy
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 1. Ce qui arrive de PredictRequest.body
    raw_text = Column(String, nullable=False)
    canal = Column(String(50), nullable=True)

    # 2. Champs remplis par votre pipeline d'enrichissement (M4)
    langue = Column(String(5), nullable=True)            # ex: 'fr', 'en'
    langue_confidence = Column(Float, nullable=True)     # ex: 0.98
    sentiment = Column(String(20), nullable=True)        # 'positif', 'negatif'
    sentiment_score = Column(Float, nullable=True)       # ex: 0.85
    routed_priority = Column(String(30), nullable=True)  # 'high_intl', 'normal'
    
    # 3. Le suivi technique de la pipeline
    enriched_at = Column(DateTime(timezone=True), nullable=True)