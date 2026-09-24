"""
TRACE - Evaluation & Research Benchmark API Endpoints
Runs and retrieves objective 3-way evaluation metrics across the Ground Truth dataset.
"""

import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.evaluation.evaluator import evaluator
from app.schemas.reconciliation import BenchmarkEvaluationReport
from app.core.config import settings

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.post("/run", response_model=BenchmarkEvaluationReport)
@router.get("/benchmark", response_model=BenchmarkEvaluationReport)
def run_evaluation_benchmark():
    """
    Executes the 3-Way Reconciliation Benchmark (RULE_BASED vs AI_LLM vs HYBRID)
    across the entire annotated Ground Truth dataset without pre-assuming any winner.
    """
    try:
        report = evaluator.run_full_benchmark()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {str(e)}")

@router.get("/results")
@router.get("/latest")
def get_latest_evaluation():
    """
    Returns the latest research evaluation metrics if already generated, otherwise runs benchmark.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    report_path = os.path.join(base_dir, "data", "ground_truth", "latest_evaluation_report.json")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Run if not yet cached
    report = evaluator.run_full_benchmark()
    return report.model_dump(mode="json")

@router.get("/ground-truth")
def get_ground_truth_dataset():
    """
    Returns the annotated ground truth benchmark transactions.
    """
    dataset = evaluator.load_benchmark_dataset()
    return {
        "dataset_size": len(dataset),
        "categories": list({txn.get("category") for txn in dataset}),
        "transactions": [
            {
                "transaction_reference": txn.get("transaction_reference"),
                "category": txn.get("category"),
                "documents_count": len(txn.get("documents", [])),
                "expected_discrepancies": txn.get("ground_truth_discrepancies", [])
            }
            for txn in dataset
        ]
    }

@router.get("/export-report", response_class=PlainTextResponse)
def export_research_report():
    """
    Exports formatted Markdown research report comparing all 3 approaches.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    report_md_path = os.path.join(base_dir, "data", "ground_truth", "evaluation_report.md")
    if not os.path.exists(report_md_path):
        evaluator.run_full_benchmark()

    with open(report_md_path, "r", encoding="utf-8") as f:
        return f.read()

@router.get("/classifier-metrics")
def get_classifier_metrics():
    """
    Returns trained document classifier performance metrics and confusion matrix.
    """
    metrics_path = os.path.join(settings.MODELS_DIR, "classifier_metrics.json")
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="Classifier metrics not found.")

    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@router.get("/ablation")
@router.post("/ablation")
def get_ablation_study():
    """
    Executes an empirical ablation study across 4 distinct configurations:
    1. Rule-Based Only
    2. Rules + FAISS Embeddings (No LLM)
    3. Rules + LLM Reasoning (No FAISS)
    4. Full Multi-Source Hybrid (TRACE)
    """
    try:
        return evaluator.run_ablation_study()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ablation study failed: {str(e)}")
