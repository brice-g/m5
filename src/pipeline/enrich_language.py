import hashlib
import time
from typing import Tuple, Optional
from loguru import logger
import fasttext

# Configuration du modèle
MODEL_PATH = "library/lid.176.bin"

class LanguageEnricher:
    def __init__(self, model_path: str = MODEL_PATH, default_threshold: float = 0.5):
        self.threshold = default_threshold
        self._cache = {}
        try:
            self.model = fasttext.load_model(model_path)
            logger.info("Modèle FastText chargé avec succès pour la détection de langue.")
        except Exception as e:
            logger.error(f"Impossible de charger le modèle Fasttext ({e}). Mode dégradation activé.")
            self.model = None

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def analyze(self, text: str, threshold: Optional[float] = None) -> Tuple[Optional[str], float]:
        if not text or not text.strip():
            return None, 0.0

        current_threshold = threshold if threshold is not None else self.threshold
        text_hash = self._get_hash(text)
        truncated_text = text[:50].replace('\n', ' ') + '...' if len(text) > 50 else text

        # 1. Vérification du Cache
        if text_hash in self._cache:
            logger.debug(f"[CACHE HIT] Langue pour: '{truncated_text}'")
            return self._cache[text_hash]

        start_time = time.perf_counter()

        # 2. Gestion du Fallback si le modèle principal est absent ou échoue
        if not self.model:
            logger.warning(f"[FALLBACK] Modèle absent pour '{truncated_text}'. Retour de None.")
            return None, 0.0

        try:
            labels, confidences = self.model.predict(text.strip(), k=1)
            # FastText retourne: (('__label__fr',), array([0.98]))
            lang = labels[0].replace('__label__', '') # type: ignore
            confidence = float(confidences[0])

            # Validation du seuil de confiance
            if confidence < current_threshold:
                logger.warning(f"[LOW CONFIDENCE] {lang} ({confidence:.2f}) < {current_threshold} pour '{truncated_text}'")
                result = (None, confidence)
            else:
                result = (lang, confidence)

        except Exception as e:
            logger.error(f"[ERROR INFERENCE] Échec de la détection de langue ({e}) pour '{truncated_text}'")
            result = (None, 0.0)

        duration = time.perf_counter() - start_time
        logger.info(f"[LANGUE] '{truncated_text}' -> {result[0]} ({result[1]:.2f}) en {duration*1000:.2f}ms")

        # Mise en cache
        self._cache[text_hash] = result
        return result