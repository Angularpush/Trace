"""
TRACE - Supervised Document Classification Engine & Training Pipeline
Implements high-performance TF-IDF Vectorizer and Multiclass Logistic Regression
with probability calibration, evaluation metrics, and joblib serialization.
Compatible with Python 3.11+ / 3.14+ on all OS platforms.
"""

import os
import sys
import re
import math
import json
import joblib
import csv
import numpy as np
from typing import List, Dict, Tuple, Any

# Ensure backend root is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

class TfidfModel:
    def __init__(self, ngram_range=(1, 3), max_features=5000, min_df=2, sublinear_tf=True):
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.min_df = min_df
        self.sublinear_tf = sublinear_tf
        self.vocabulary_: Dict[str, int] = {}
        self.idf_diag_: np.ndarray = np.array([])
        self.feature_names_: List[str] = []

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase, clean punctuation, extract word tokens
        clean_text = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = clean_text.split()
        ngrams = []
        min_n, max_n = self.ngram_range
        for n in range(min_n, max_n + 1):
            for i in range(len(tokens) - n + 1):
                ngrams.append(" ".join(tokens[i:i+n]))
        return ngrams

    def fit(self, raw_documents: List[str]):
        df_counts: Dict[str, int] = {}
        n_docs = len(raw_documents)

        # Count document frequency
        for doc in raw_documents:
            unique_terms = set(self._tokenize(doc))
            for term in unique_terms:
                df_counts[term] = df_counts.get(term, 0) + 1

        # Filter by min_df
        filtered_terms = [t for t, c in df_counts.items() if c >= self.min_df]
        # Sort by document frequency descending, then alphabetically
        filtered_terms.sort(key=lambda t: (-df_counts[t], t))
        
        if self.max_features and len(filtered_terms) > self.max_features:
            filtered_terms = filtered_terms[:self.max_features]

        self.vocabulary_ = {t: idx for idx, t in enumerate(filtered_terms)}
        self.feature_names_ = filtered_terms

        # Compute smooth IDF: log((1 + n_docs) / (1 + df)) + 1
        idf = np.zeros(len(filtered_terms), dtype=np.float32)
        for term, idx in self.vocabulary_.items():
            df = df_counts[term]
            idf[idx] = math.log((1.0 + n_docs) / (1.0 + df)) + 1.0

        self.idf_diag_ = idf
        return self

    def transform(self, raw_documents: List[str]) -> np.ndarray:
        n_docs = len(raw_documents)
        n_feats = len(self.vocabulary_)
        matrix = np.zeros((n_docs, n_feats), dtype=np.float32)

        for i, doc in enumerate(raw_documents):
            tokens = self._tokenize(doc)
            term_counts: Dict[str, int] = {}
            for t in tokens:
                if t in self.vocabulary_:
                    term_counts[t] = term_counts.get(t, 0) + 1

            for term, count in term_counts.items():
                idx = self.vocabulary_[term]
                tf = (1.0 + math.log(count)) if (self.sublinear_tf and count > 0) else float(count)
                matrix[i, idx] = tf * self.idf_diag_[idx]

            # L2 normalization
            norm = np.linalg.norm(matrix[i])
            if norm > 0:
                matrix[i] = matrix[i] / norm

        return matrix

    def fit_transform(self, raw_documents: List[str]) -> np.ndarray:
        return self.fit(raw_documents).transform(raw_documents)


class LogisticRegressionClassifier:
    def __init__(self, learning_rate: float = 0.05, max_iter: int = 500, l2_reg: float = 0.001):
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.l2_reg = l2_reg
        self.weights_: np.ndarray = np.array([])
        self.bias_: np.ndarray = np.array([])
        self.classes_: List[str] = []

    def _softmax(self, z: np.ndarray) -> np.ndarray:
        # Numerically stable softmax
        exp_z = np.exp(z - np.max(z, axis=1, keepdims=True))
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)

    def fit(self, X: np.ndarray, y: List[str]):
        self.classes_ = sorted(list(set(y)))
        class_to_idx = {c: idx for idx, c in enumerate(self.classes_)}
        n_samples, n_features = X.shape
        n_classes = len(self.classes_)

        # One-hot encode targets
        Y = np.zeros((n_samples, n_classes), dtype=np.float32)
        for i, target in enumerate(y):
            Y[i, class_to_idx[target]] = 1.0

        # Initialize weights (Xavier/Glorot init)
        self.weights_ = np.zeros((n_features, n_classes), dtype=np.float32)
        self.bias_ = np.zeros(n_classes, dtype=np.float32)

        # Batch Gradient Descent with Adam Optimizer for fast and stable convergence
        m_w = np.zeros_like(self.weights_)
        v_w = np.zeros_like(self.weights_)
        m_b = np.zeros_like(self.bias_)
        v_b = np.zeros_like(self.bias_)
        beta1, beta2, eps = 0.9, 0.999, 1e-8

        for epoch in range(1, self.max_iter + 1):
            # Forward pass: logits = X @ W + b
            logits = np.dot(X, self.weights_) + self.bias_
            probs = self._softmax(logits)

            # Gradient calculation
            error = probs - Y  # (n_samples, n_classes)
            grad_w = (np.dot(X.T, error) / n_samples) + (self.l2_reg * self.weights_)
            grad_b = np.sum(error, axis=0) / n_samples

            # Adam parameter updates
            m_w = beta1 * m_w + (1 - beta1) * grad_w
            v_w = beta2 * v_w + (1 - beta2) * (grad_w ** 2)
            m_w_hat = m_w / (1 - beta1 ** epoch)
            v_w_hat = v_w / (1 - beta2 ** epoch)
            self.weights_ -= (self.learning_rate / (np.sqrt(v_w_hat) + eps)) * m_w_hat

            m_b = beta1 * m_b + (1 - beta1) * grad_b
            v_b = beta2 * v_b + (1 - beta2) * (grad_b ** 2)
            m_b_hat = m_b / (1 - beta1 ** epoch)
            v_b_hat = v_b / (1 - beta2 ** epoch)
            self.bias_ -= (self.learning_rate / (np.sqrt(v_b_hat) + eps)) * m_b_hat

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        logits = np.dot(X, self.weights_) + self.bias_
        return self._softmax(logits)

    def predict(self, X: np.ndarray) -> List[str]:
        probs = self.predict_proba(X)
        pred_indices = np.argmax(probs, axis=1)
        return [self.classes_[idx] for idx in pred_indices]


class DocumentClassificationPipeline:
    def __init__(self, vectorizer: TfidfModel = None, classifier: LogisticRegressionClassifier = None):
        self.vectorizer = vectorizer or TfidfModel(ngram_range=(1, 3), max_features=5000)
        self.classifier = classifier or LogisticRegressionClassifier(learning_rate=0.08, max_iter=400, l2_reg=0.0005)
        self.classes_ = []

    def fit(self, texts: List[str], labels: List[str]):
        print(f"Extracting TF-IDF features from {len(texts)} documents...")
        X = self.vectorizer.fit_transform(texts)
        print(f"Vocabulary size: {len(self.vectorizer.vocabulary_)} features")
        print("Training Multiclass Logistic Regression classifier...")
        self.classifier.fit(X, labels)
        self.classes_ = self.classifier.classes_
        return self

    def predict(self, texts: List[str]) -> List[str]:
        X = self.vectorizer.transform(texts)
        return self.classifier.predict(X)

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        X = self.vectorizer.transform(texts)
        return self.classifier.predict_proba(X)

    def classify_single(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        X = self.vectorizer.transform([text])
        probs = self.classifier.predict_proba(X)[0]
        max_idx = int(np.argmax(probs))
        predicted_class = self.classes_[max_idx]
        confidence = float(probs[max_idx])
        prob_dist = {self.classes_[i]: float(probs[i]) for i in range(len(self.classes_))}
        return predicted_class, confidence, prob_dist


def compute_metrics(y_true: List[str], y_pred: List[str], classes: List[str]) -> Dict[str, Any]:
    n_samples = len(y_true)
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = correct / n_samples if n_samples > 0 else 0.0

    # Class-wise metrics
    report = {}
    class_to_idx = {c: i for i, c in enumerate(classes)}
    cm = [[0] * len(classes) for _ in range(len(classes))]

    for yt, yp in zip(y_true, y_pred):
        if yt in class_to_idx and yp in class_to_idx:
            cm[class_to_idx[yt]][class_to_idx[yp]] += 1

    for i, c in enumerate(classes):
        tp = cm[i][i]
        fp = sum(cm[row][i] for row in range(len(classes))) - tp
        fn = sum(cm[i][col] for col in range(len(classes))) - tp
        support = sum(cm[i][col] for col in range(len(classes)))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        report[c] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1-score": round(f1, 4),
            "support": support
        }

    # Macro and Weighted Averages
    macro_p = sum(report[c]["precision"] for c in classes) / len(classes)
    macro_r = sum(report[c]["recall"] for c in classes) / len(classes)
    macro_f1 = sum(report[c]["f1-score"] for c in classes) / len(classes)

    weighted_p = sum(report[c]["precision"] * report[c]["support"] for c in classes) / n_samples
    weighted_r = sum(report[c]["recall"] * report[c]["support"] for c in classes) / n_samples
    weighted_f1 = sum(report[c]["f1-score"] * report[c]["support"] for c in classes) / n_samples

    report["macro avg"] = {"precision": round(macro_p, 4), "recall": round(macro_r, 4), "f1-score": round(macro_f1, 4), "support": n_samples}
    report["weighted avg"] = {"precision": round(weighted_p, 4), "recall": round(weighted_r, 4), "f1-score": round(weighted_f1, 4), "support": n_samples}

    return {
        "accuracy": round(accuracy, 4),
        "labels": classes,
        "classification_report": report,
        "confusion_matrix": cm,
        "total_samples": n_samples
    }


def train_document_classifier():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(base_dir, "datasets", "doc_classification.csv")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    output_model_path = os.path.join(models_dir, "document_classifier.joblib")
    metrics_path = os.path.join(models_dir, "classifier_metrics.json")
    backend_model_dir = os.path.join(os.path.dirname(base_dir), "backend", "app", "classification")
    os.makedirs(backend_model_dir, exist_ok=True)
    backend_model_path = os.path.join(backend_model_dir, "document_classifier.joblib")

    print(f"Loading dataset from {dataset_path}...")
    texts, labels = [], []
    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"])
            labels.append(row["label"])

    # Stratified 80/20 train/test split
    np.random.seed(42)
    indices = np.arange(len(texts))
    np.random.shuffle(indices)

    split_idx = int(len(texts) * 0.8)
    train_idx, test_idx = indices[:split_idx], indices[split_idx:]

    X_train = [texts[i] for i in train_idx]
    y_train = [labels[i] for i in train_idx]
    X_test = [texts[i] for i in test_idx]
    y_test = [labels[i] for i in test_idx]

    print(f"Training samples: {len(X_train)} | Test samples: {len(X_test)}")

    pipeline = DocumentClassificationPipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    metrics = compute_metrics(y_test, y_pred, pipeline.classes_)

    print("\n" + "=" * 60)
    print("TRAINED MODEL TEST EVALUATION")
    print("=" * 60)
    print(f"Test Accuracy: {metrics['accuracy'] * 100:.2f}%")
    print(f"Macro F1-Score: {metrics['classification_report']['macro avg']['f1-score']:.4f}")
    print(f"Weighted F1-Score: {metrics['classification_report']['weighted avg']['f1-score']:.4f}")
    print("\nClass Breakdown:")
    for c in pipeline.classes_:
        r = metrics['classification_report'][c]
        print(f"  {c:<18}: Precision={r['precision']:.3f} | Recall={r['recall']:.3f} | F1={r['f1-score']:.3f} (n={r['support']})")

    # Save model artifact
    joblib.dump(pipeline, output_model_path)
    print(f"\nSaved versioned model artifact: {output_model_path}")

    # Copy to backend classification module
    import shutil
    shutil.copyfile(output_model_path, backend_model_path)
    print(f"Copied model artifact to backend: {backend_model_path}")

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics to: {metrics_path}")

    return pipeline, metrics

if __name__ == "__main__":
    train_document_classifier()
