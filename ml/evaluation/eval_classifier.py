"""
TRACE - Document Classifier Evaluation Script
Evaluates trained joblib model on full/test dataset with detailed Precision, Recall, F1, Confusion Matrix.
"""

import os
import sys
import json
import joblib
import csv
import numpy as np

# Ensure training module classes are importable for joblib deserialization
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from training.train_classifier import (
    DocumentClassificationPipeline,
    TfidfModel,
    LogisticRegressionClassifier,
    compute_metrics
)

def evaluate_classifier():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_dir, "models", "document_classifier.joblib")
    dataset_path = os.path.join(base_dir, "datasets", "doc_classification.csv")

    if not os.path.exists(model_path):
        print(f"Error: Model artifact not found at {model_path}. Run training first.")
        return None

    model: DocumentClassificationPipeline = joblib.load(model_path)
    
    texts, labels = [], []
    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"])
            labels.append(row["label"])

    y_pred = model.predict(texts)
    metrics = compute_metrics(labels, y_pred, model.classes_)

    print("=" * 65)
    print("TRACE DOCUMENT CLASSIFIER EVALUATION REPORT")
    print("=" * 65)
    print(f"Total Evaluated Samples : {metrics['total_samples']}")
    print(f"Overall Accuracy        : {metrics['accuracy'] * 100:.2f}%")
    print(f"Macro F1-Score          : {metrics['classification_report']['macro avg']['f1-score']:.4f}")
    print(f"Weighted F1-Score       : {metrics['classification_report']['weighted avg']['f1-score']:.4f}")
    print("\nClass-level Breakdown:")
    for c in model.classes_:
        r = metrics['classification_report'][c]
        print(f"  {c:<18}: Precision={r['precision']:.3f} | Recall={r['recall']:.3f} | F1={r['f1-score']:.3f} | Support={r['support']}")

    print("\nConfusion Matrix:")
    print("Classes: " + ", ".join(model.classes_))
    for row in metrics["confusion_matrix"]:
        print("  " + str(row))
    print("=" * 65)

    return metrics

if __name__ == "__main__":
    evaluate_classifier()
