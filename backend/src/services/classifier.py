"""
Model loading and inference.

Fixes carried over from the old inline code in backend/app.py:

* The model was loaded from the CWD-relative path
  "backend/models/deep/bilstm_model.h5", so it only resolved when the process
  was started from the project root.  It uses `paths.deep_model_path()` now.
* When loading failed, `model_wrapper.model` stayed None and the first request
  died with an AttributeError -> HTML 500.  `ensure_ready()` raises a proper
  503 instead.
* Keras predict calls are serialised with a lock; the dev server is threaded
  and a background retrain can swap the model out mid-request.
"""

import threading
import time

import numpy as np

from backend.src.api.errors import ServiceUnavailable
from backend.src.data.langid import detect_language_strict
from backend.src.data.preprocess import clean_text
from backend.src.models.bilstm import DeepModel
from backend.src.utils import paths

MODEL_NAME = "BiLSTM"
ARCHITECTURE = "bilstm"

# Romanised Hindi function words. Their presence means the text is Hinglish
# rather than English, which `detect_language_strict` cannot tell from script
# alone. Kept here as data instead of an inline generator duplicated per route.
HINGLISH_MARKERS = (
    "hai", "nahi", "nahin", "tum", "aap", "kya", "kyu", "kyun",
    "mera", "tera", "hum", "kar", "raha", "rahi", "bhai", "yaar",
)


class Classifier:
    def __init__(self):
        self._wrapper = None
        self._lock = threading.Lock()
        self._load_error = None

    # --- lifecycle ---------------------------------------------------------

    def load(self):
        """
        Load tokenizer + weights. Records the failure rather than raising so a
        missing model degrades the prediction endpoints only, not the whole API.
        """
        from tensorflow.keras.models import load_model

        with self._lock:
            self._load_error = None
            try:
                wrapper = DeepModel(architecture=ARCHITECTURE)
                wrapper.load_tokenizer()

                model_path = paths.deep_model_path(ARCHITECTURE)
                wrapper.model = load_model(model_path)

                self._wrapper = wrapper
                print(f"  [Classifier] {MODEL_NAME} loaded from {model_path}")
                return True

            except Exception as exc:
                self._wrapper = None
                self._load_error = f"{type(exc).__name__}: {exc}"
                print(f"  [Classifier] Load failed: {self._load_error}")
                return False

    def reload(self):
        """Pick up newly trained weights (called after a training job)."""
        print("  [Classifier] Reloading model after training...")
        return self.load()

    # --- state -------------------------------------------------------------

    @property
    def is_ready(self):
        return self._wrapper is not None and self._wrapper.model is not None

    @property
    def load_error(self):
        return self._load_error

    def ensure_ready(self):
        if not self.is_ready:
            raise ServiceUnavailable(
                "The classification model is not loaded. Train the model "
                "(python -m backend.src.training.train) and restart the API.",
                code="model_unavailable",
                details={"reason": self._load_error} if self._load_error else None,
            )

    def status(self):
        return {
            "model": MODEL_NAME,
            "architecture": ARCHITECTURE,
            "loaded": self.is_ready,
            "error": self._load_error,
        }

    # --- inference ---------------------------------------------------------

    @staticmethod
    def detect_language(cleaned_text):
        lowered = cleaned_text.lower()
        origin = (
            "indo_mixed"
            if any(marker in lowered.split() for marker in HINGLISH_MARKERS)
            else "english"
        )
        return detect_language_strict(cleaned_text, origin)

    def classify(self, text):
        """
        Run the full pipeline for one string.

        Returns a dict with label, confidence, per-class probabilities, detected
        language and measured latency. Does not touch the database.
        """
        self.ensure_ready()

        started = time.perf_counter()

        cleaned = clean_text(text)
        language = self.detect_language(cleaned)

        with self._lock:
            # Re-check: a reload may have completed while we waited.
            if not self.is_ready:
                self.ensure_ready()
            sequences = self._wrapper.preprocess([cleaned])
            probabilities = self._wrapper.model.predict(sequences, verbose=0)[0]

        label = int(np.argmax(probabilities))
        latency_ms = int((time.perf_counter() - started) * 1000)

        return {
            "label": label,
            "confidence": float(probabilities[label]),
            "probabilities": [float(value) for value in probabilities],
            "language": language,
            "cleaned_text": cleaned,
            "latency_ms": latency_ms,
            "model_name": MODEL_NAME,
        }


# Module-level singleton; the Flask app factory calls .load() once at startup.
classifier = Classifier()
