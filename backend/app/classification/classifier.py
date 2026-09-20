"""
TRACE - Document Classification Service
Inference service loading versioned TF-IDF + Logistic Regression model artifact from ml/models/document_classifier.joblib.
"""

import os
import sys
import joblib
import numpy as np
from typing import Tuple, Dict, Any, Optional

# Ensure classification pipeline class is imported for unpickling
backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
project_root = os.path.dirname(backend_root)
ml_dir = os.path.join(project_root, "ml")
if ml_dir not in sys.path:
    sys.path.insert(0, ml_dir)

from training.train_classifier import (
    DocumentClassificationPipeline,
    TfidfModel,
    LogisticRegressionClassifier
)

# Register in main module so unpickling works regardless of invocation context
main_mod = sys.modules.get('__main__')
if main_mod:
    setattr(main_mod, 'DocumentClassificationPipeline', DocumentClassificationPipeline)
    setattr(main_mod, 'TfidfModel', TfidfModel)
    setattr(main_mod, 'LogisticRegressionClassifier', LogisticRegressionClassifier)


class DocumentClassificationService:
    """
    TRACE Document Classification Service
    Loads trained TF-IDF + Logistic Regression model from ml/models/document_classifier.joblib.
    Executes inference and returns predicted document type and mathematical confidence probability.
    Raises explicit backend errors if model artifact is missing (no silent fake fallbacks).
    """
    _instance: Optional["DocumentClassificationService"] = None
    _model: Optional[DocumentClassificationPipeline] = None
    _model_path: Optional[str] = None
    _load_error: Optional[str] = None

    def __init__(self, model_path: Optional[str] = None):
        self._model = None
        self._model_path = None
        self._load_error = None
        self.load_model(model_path)

    @classmethod
    def get_instance(cls, model_path: Optional[str] = None) -> "DocumentClassificationService":
        if cls._instance is None:
            cls._instance = cls(model_path)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Helper for testing or reloading models dynamically."""
        cls._instance = None

    def load_model(self, custom_path: Optional[str] = None):
        """
        Resolves model artifact:
        - If custom_path is provided, strictly load from that path.
        - Otherwise, search standard locations:
          1. ml/models/document_classifier.joblib
          2. backend/app/classification/document_classifier.joblib
        """
        if custom_path:
            search_paths = [custom_path]
        else:
            search_paths = [
                os.path.abspath(os.path.join(project_root, "ml", "models", "document_classifier.joblib")),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "document_classifier.joblib"))
            ]

        resolved_path = None
        for p in search_paths:
            if os.path.exists(p):
                resolved_path = p
                break

        if not resolved_path:
            self._model = None
            self._load_error = (
                f"Document classification model 'document_classifier.joblib' is missing. "
                f"Searched in: {search_paths}. Please run the training pipeline to generate the artifact."
            )
            return

        try:
            self._model = joblib.load(resolved_path)
            self._model_path = resolved_path
            self._load_error = None
            print(f"[DocumentClassificationService] Successfully loaded model from {resolved_path}")
        except Exception as e:
            self._model = None
            self._load_error = f"Failed to load document classification model from {resolved_path}: {str(e)}"
            print(f"[DocumentClassificationService] Error loading model: {self._load_error}")

    def is_model_loaded(self) -> bool:
        return self._model is not None

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "loaded": self.is_model_loaded(),
            "model_path": self._model_path,
            "error": self._load_error,
            "classes": getattr(self._model, "classes_", []) if self._model else []
        }

    def classify(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Classifies document text using the trained TF-IDF + Logistic Regression model.

        Returns:
            Tuple[str, float, Dict[str, float]]: (predicted_doc_type, confidence_probability, probability_distribution)

        Raises:
            RuntimeError: If model is missing or failed to load.
        """
        if not text or not text.strip():
            return "UNKNOWN", 0.0, {}

        if self._model is None:
            err = self._load_error or "Document classification model 'document_classifier.joblib' is missing."
            raise RuntimeError(
                f"[DocumentClassificationService] Cannot classify document: {err}"
            )

        if hasattr(self._model, "classify_single"):
            return self._model.classify_single(text)
        elif hasattr(self._model, "predict_proba"):
            probs = self._model.predict_proba([text])[0]
            classes = getattr(self._model, "classes_", [])
            max_idx = int(np.argmax(probs))
            pred_class = classes[max_idx] if max_idx < len(classes) else "UNKNOWN"
            conf = float(probs[max_idx])
            dist = {classes[i]: float(probs[i]) for i in range(len(classes))}
            return pred_class, conf, dist
        else:
            raise RuntimeError(
                "[DocumentClassificationService] Loaded model does not implement classify_single or predict_proba."
            )


# Aliases for backward compatibility
DocumentClassifierService = DocumentClassificationService
classifier_service = DocumentClassificationService.get_instance()
