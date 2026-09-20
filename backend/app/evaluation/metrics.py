"""
TRACE - Benchmark Evaluation Metrics
Calculates true Precision, Recall, F1, Reconciliation Accuracy, and Evidence Accuracy.
"""

from typing import List, Dict, Any, Set

class BenchmarkMetricsCalculator:
    @staticmethod
    def calculate_discrepancy_metrics(
        ground_truth_discrepancies: List[str],  # list of expected rule_codes or types
        predicted_discrepancies: List[str]
    ) -> Dict[str, float]:
        gt_set: Set[str] = set(ground_truth_discrepancies)
        pred_set: Set[str] = set(predicted_discrepancies)

        if not gt_set and not pred_set:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": 0, "fp": 0, "fn": 0}

        tp = len(gt_set.intersection(pred_set))
        fp = len(pred_set - gt_set)
        fn = len(gt_set - pred_set)

        precision = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if not pred_set else 0.0)
        recall = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if not gt_set else 0.0)
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "tp": tp,
            "fp": fp,
            "fn": fn
        }

    @staticmethod
    def calculate_evidence_accuracy(
        predicted_evidence_snippets: List[str],
        ground_truth_fields: List[str]
    ) -> float:
        if not ground_truth_fields:
            return 1.0
        if not predicted_evidence_snippets:
            return 0.0

        matched = 0
        for f in ground_truth_fields:
            if any(f.lower() in s.lower() for s in predicted_evidence_snippets):
                matched += 1
        return round(matched / len(ground_truth_fields), 4)
