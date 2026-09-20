"""
TRACE - Semantic Matching Evaluation Pipeline
Evaluates pretrained Sentence Transformer (sentence-transformers/all-MiniLM-L6-v2)
on labelled MSME entity pairs (Suppliers, Items, Documents).
"""

import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics import precision_recall_fscore_support, accuracy_score, roc_auc_score

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))

def evaluate_pair_dataset(model: SentenceTransformer, file_path: str, dataset_name: str, threshold: float = 0.70):
    if not os.path.exists(file_path):
        print(f"Dataset not found: {file_path}")
        return None
    
    df = pd.read_csv(file_path)
    similarities = []
    
    for _, row in df.iterrows():
        emb_a = model.encode(str(row["text_a"]), normalize_embeddings=True)
        emb_b = model.encode(str(row["text_b"]), normalize_embeddings=True)
        sim = float(np.dot(emb_a, emb_b))
        similarities.append(sim)
        
    df["similarity"] = similarities
    df["pred_label"] = (df["similarity"] >= threshold).astype(int)
    
    y_true = df["label"].values
    y_pred = df["pred_label"].values
    
    acc = accuracy_score(y_true, y_pred)
    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
    try:
        auc = roc_auc_score(y_true, df["similarity"].values)
    except Exception:
        auc = 0.0

    print(f"\n--- Evaluation Results for {dataset_name} (Threshold = {threshold:.2f}) ---")
    print(f"Samples: {len(df)} | Accuracy: {acc * 100:.2f}% | Precision: {p:.3f} | Recall: {r:.3f} | F1: {f1:.3f} | ROC-AUC: {auc:.3f}")
    
    # Print examples
    print("Sample Matches:")
    for _, r_row in df.head(3).iterrows():
        print(f"  [{r_row['label']} vs Pred:{r_row['pred_label']}] Sim: {r_row['similarity']:.3f} | A: {r_row['text_a']} | B: {r_row['text_b']}")

    return {
        "dataset": dataset_name,
        "samples": len(df),
        "threshold": threshold,
        "accuracy": acc,
        "precision": p,
        "recall": r,
        "f1": f1,
        "roc_auc": auc
    }

def run_semantic_evaluation():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ds_dir = os.path.join(base_dir, "datasets")
    
    print("Loading pretrained SentenceTransformer: sentence-transformers/all-MiniLM-L6-v2...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    results = {}
    results["suppliers"] = evaluate_pair_dataset(
        model, os.path.join(ds_dir, "supplier_pairs.csv"), "Supplier Entity Matching", threshold=0.72
    )
    results["items"] = evaluate_pair_dataset(
        model, os.path.join(ds_dir, "item_pairs.csv"), "Line Item Matching", threshold=0.68
    )
    results["documents"] = evaluate_pair_dataset(
        model, os.path.join(ds_dir, "document_pairs.csv"), "Document Relationship Matching", threshold=0.65
    )
    return results

if __name__ == "__main__":
    run_semantic_evaluation()
