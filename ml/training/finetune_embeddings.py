"""
TRACE - Optional Sentence Transformer Fine-Tuning Pipeline
Uses MultipleNegativesRankingLoss / CosineSimilarityLoss on MSME entity pairs.
This pipeline is OPTIONAL and only executed when fine-tuning is explicitly initiated.
"""

import os
import pandas as pd
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

def finetune_msme_embeddings(
    output_dir: str = "ml/models/msme_minilm_finetuned",
    epochs: int = 3,
    batch_size: int = 16
):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ds_dir = os.path.join(base_dir, "datasets")
    
    # Load pairs
    supplier_df = pd.read_csv(os.path.join(ds_dir, "supplier_pairs.csv"))
    item_df = pd.read_csv(os.path.join(ds_dir, "item_pairs.csv"))
    doc_df = pd.read_csv(os.path.join(ds_dir, "document_pairs.csv"))
    
    combined_df = pd.concat([supplier_df, item_df, doc_df], ignore_index=True)
    
    train_examples = []
    for _, row in combined_df.iterrows():
        train_examples.append(
            InputExample(texts=[str(row["text_a"]), str(row["text_b"])], label=float(row["label"]))
        )
    
    print(f"Loaded {len(train_examples)} pair examples for fine-tuning...")
    
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
    train_loss = losses.CosineSimilarityLoss(model=model)
    
    target_path = os.path.join(base_dir, "models", "msme_minilm_finetuned")
    os.makedirs(target_path, exist_ok=True)
    
    print(f"Starting fine-tuning for {epochs} epochs...")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        warmup_steps=10,
        output_path=target_path
    )
    print(f"Fine-tuned model successfully saved to: {target_path}")
    return target_path

if __name__ == "__main__":
    finetune_msme_embeddings()
