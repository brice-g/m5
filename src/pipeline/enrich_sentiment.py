import hashlib
import time
from typing import Tuple, Optional
from loguru import logger
from transformers import pipeline

class SentimentEnricher:
    def __init__(self, model_name_or_path: str = "tblard/tf-allocine", default_threshold: float = 0.5):
        self.threshold = default_threshold
        self._cache = {}
        try:
            # Chargement du pipeline Hugging Face (ex: CamemBERT fine-tuned)
            self.classifier = pipeline("text-classification", model=model_name_or_path, device=-1)
            logger.info(f"Modèle de sentiment {model_name_or_path} chargé avec succès.")
        except Exception as e:
            logger.error(f"Impossible de charger le modèle de sentiment ({e}). Mode dégradation activé.")
            self.classifier = None

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _map_label(self, raw_label: str) -> str:
        """
        Mapping des sorties du modèle. 
        S'adapte aux modèles binaires (Allocine) ou multi-classes.
        """
        mapping = {
            "POSITIVE": "positif",
            "NEGATIVE": "negatif",
            "NEUTRAL": "neutre",
            "LABEL_2": "positif",
            "LABEL_1": "neutre",
            "LABEL_0": "negatif",
            "1-star": "negatif",
            "2-star": "negatif",
            "3-star": "neutre",
            "4-star": "positif",
            "5-star": "positif"
        }
        return mapping.get(raw_label.upper(), "neutre")

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
            sentiment_mapped = self._map_label(outputs['label'])
            score = float(outputs['score'])
            result = (sentiment_mapped, score)
        except Exception as e:
            logger.error(f"[ERROR INFERENCE] Échec de l'analyse de sentiment ({e}) pour '{truncated_text}'")
            result = (None, 0.0)

        duration = time.perf_counter() - start_time
        logger.info(f"[SENTIMENT] '{truncated_text}' -> {result[0]} ({result[1]:.2f}) en {duration*1000:.2f}ms")

        self._cache[text_hash] = result
        return result