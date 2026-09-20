"""
TRACE - Vector Index Store
FAISS-backed fast cosine similarity search for entity and document retrieval.
"""

import numpy as np
from typing import List, Tuple, Dict, Any

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from app.semantic.embeddings import embedding_service

class VectorStore:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.documents: List[Dict[str, Any]] = []
        self.vectors: np.ndarray = np.empty((0, dimension), dtype=np.float32)
        self.use_faiss = FAISS_AVAILABLE
        self.index = None
        if self.use_faiss:
            try:
                self.index = faiss.IndexFlatIP(dimension)
            except Exception as e:
                print(f"[VectorStore] FAISS init error: {e}, falling back to numpy")
                self.use_faiss = False

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] = None):
        if not texts:
            return
        embeddings = embedding_service.encode(texts)
        if metadatas is None:
            metadatas = [{} for _ in texts]

        for i, text in enumerate(texts):
            doc = {"text": text, "metadata": metadatas[i]}
            self.documents.append(doc)

        if self.use_faiss and self.index is not None:
            self.index.add(embeddings)
        else:
            if len(self.vectors) == 0:
                self.vectors = embeddings
            else:
                self.vectors = np.vstack([self.vectors, embeddings])

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if not self.documents:
            return []

        query_vec = embedding_service.encode([query])
        top_k = min(top_k, len(self.documents))

        if self.use_faiss and self.index is not None:
            scores, indices = self.index.search(query_vec, top_k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.documents):
                    results.append((self.documents[idx], float(score)))
            return results
        else:
            # Numpy cosine similarity
            sims = np.dot(self.vectors, query_vec[0])
            top_indices = np.argsort(sims)[::-1][:top_k]
            return [(self.documents[idx], float(sims[idx])) for idx in top_indices]
