#faiss category, embeddings going in and coming out with postgres using its faiss id

import os
import threading
import numpy as np
import faiss
from typing import Any, cast

from config import settings

_lock = threading.Lock()  # FAISS index is not thread-safe for writes


class VectorStore:
    def __init__(self, dim: int = settings.faiss_dim, path: str = settings.faiss_index_path):
        self.dim = dim
        self.path = path
        # IndexIDMap lets us assign our own integer ids (== faiss_index_id in Postgres)
        # instead of relying on FAISS's implicit sequential ordering.
        base_index = faiss.IndexFlatIP(dim)
        self.index = faiss.IndexIDMap(base_index)
        self._load_if_exists()

    def _load_if_exists(self):
        if os.path.exists(self.path):
            self.index = faiss.read_index(self.path)

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        faiss.write_index(self.index, self.path)

    def add(self, vector: np.ndarray, faiss_id: int):
        #vector must already be L2-normalized (cosine via inner product).

        with _lock:
            v = vector.reshape(1, -1).astype("float32")
            self.index.add_with_ids(v, np.array([faiss_id], dtype="int64"))
            self.save()

    def search(self, vector: np.ndarray, top_k: int = 1):
        #Returns list of (faiss_id, similarity_score), best first.
        v = vector.reshape(1, -1).astype("float32")
        scores, ids = self.index.search(v, top_k)
        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue
            results.append((int(idx), float(score)))
        return results

    def remove(self, faiss_id: int):
        #Used on periodic rebuilds to purge soft-deleted vectors.
        with _lock:
            ids = np.array(faiss_id, dtype="int64")
            self.index.remove_ids(cast(Any, ids))
            self.save()


vector_store = VectorStore()
