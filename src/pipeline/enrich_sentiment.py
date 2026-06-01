import hashlib
import time
from typing import Tuple, Optional
from loguru import logger
from transformers import pipeline

class SentimentEnricher:
    def __init__(self, model_name_or_path: str = "cmarkea/distilcamembert-base-sentiment", default_threshold: float = 0.5):
        self.threshold = default_threshold
        self._cache = {}
        try:
            # Chargement du pipeline Hugging Face avec le modèle distilcamembert_base_sentiment
            self.classifier = pipeline("text-classification", model=model_name_or_path, device=-1)
            logger.info(f"Modèle de sentiment {model_name_or_path} chargé avec succès.")
        except Exception as e:
            logger.error(f"Impossible de charger le modèle de sentiment ({e}). Mode dégradation activé.")
            self.classifier = None

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _map_label(self, raw_label: str) -> str:
        """
        Mapping adapté spécifiquement pour cmarkea/distilcamembert-base-sentiment.
        Ce modèle utilise une classification à 5 niveaux (de 1 à 5 étoiles ou LABEL_0 à LABEL_4).
        """
        # Nettoyage de la chaîne reçue
        clean_label = raw_label.upper().replace(" ", "").replace("-", "").rstrip("S")

        mapping = {
            # Si le modèle renvoie des labels brute d'index (0 à 4)
            "LABEL_0": "negatif",  # 1 étoile
            "LABEL_1": "negatif",  # 2 étoiles
            "LABEL_2": "neutre",   # 3 étoiles
            "LABEL_3": "positif",  # 4 étoiles
            "LABEL_4": "positif",  # 5 étoiles
            
            # Si le modèle renvoie le format textuel d'étoiles
            "1STAR": "negatif",
            "2STAR": "negatif",
            "3STAR": "neutre",
            "4STAR": "positif",
            "5STAR": "positif",
        }

        # Si le label n'est pas trouvé, on renvoie "neutre" par défaut
        return mapping.get(clean_label, "neutre")

    def analyze(self, text: str, lang: Optional[str]) -> Tuple[Optional[str], float]:
        if not text or not text.strip():
            return None, 0.0

        # Règle métier : Analyse uniquement sur les textes identifiés en Français
        if lang != 'fr':
            logger.debug(f"[SKIP SENTIMENT] Langue '{lang}' non prise en charge.")
            return None, 0.0

        text_hash = self._get_hash(text)
        truncated_text = text[:50].replace('\n', ' ') + '...' if len(text) > 50 else text

        if text_hash in self._cache:
            logger.debug(f"[CACHE HIT] Sentiment pour: '{truncated_text}'")
            return self._cache[text_hash]

        if not self.classifier:
            logger.warning(f"[FALLBACK] Modèle sentiment absent. Retour de None.")
            return None, 0.0

        start_time = time.perf_counter()

        try:
            # Inférence
            outputs = self.classifier(text.strip())[0]
            score = float(outputs['score'])

            # Application de la règle du seuil de sécurité
            if score < self.threshold:
                logger.warning(f"[LOW CONFIDENCE] Score de {score:.2f} inférieur au seuil ({self.threshold}). Sentiment forcé à 'neutre'.")
                sentiment_mapped = "neutre"
            else:
                sentiment_mapped = self._map_label(outputs['label'])
                
            result = (sentiment_mapped, score)
            
        except Exception as e:
            logger.error(f"[ERROR INFERENCE] Échec de l'analyse de sentiment ({e}) pour '{truncated_text}'")
            result = (None, 0.0)

        duration = time.perf_counter() - start_time
        logger.info(f"[SENTIMENT] '{truncated_text}' -> {result[0]} ({result[1]:.2f}) en {duration*1000:.2f}ms")

        self._cache[text_hash] = result
        return result