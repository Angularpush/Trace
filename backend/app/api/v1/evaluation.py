"""
TRACE - Evaluation & Benchmark API Endpoints
Provides real-time execution and cached metrics for Document Classification and 3-Way Reconciliation Benchmark.
"""

import os
import json
from fastapi import APIRouter, HTTPException
from app.evaluation.benchmark import BenchmarkRunner
from app.core.config import settings

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

_cached_benchmark = None

@router.post("/run")
@router.get("/benchmark")
def run_evaluation_benchmark():
    """
    Executes and returns the 3-Way Reconciliation Benchmark (RULE_BASED vs AI_ONLY vs HYBRID).
    """
    global _cached_benchmark
    try:
        results = BenchmarkRunner.run_benchmark()
        _cached_benchmark = results
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {str(e)}")

@router.get("/results")
@router.get("/latest")
def get_latest_evaluation():
    """
    Returns the latest evaluation results if already performed, otherwise returns null.
    """
    global _cached_benchmark
    return _cached_benchmark

@router.get("/classifier-metrics")
def get_classifier_metrics():
    """
    Returns genuine trained classifier metrics, classification report, and confusion matrix.
    """
    metrics_path = os.path.join(settings.MODELS_DIR, "classifier_metrics.json")
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="Classifier metrics not found. Run training first.")

    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
