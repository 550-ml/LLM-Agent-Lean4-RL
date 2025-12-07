import logging
from pathlib import Path
from typing import Dict, List

import faiss
from datasets import load_dataset
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class RetrieverAgent:
    """
    定理检索，从建立好向量库检索对应定理
    """

    def __init__(
        self,
        index_dir: str = "data/retriever",
        model_name: str = "all-mpnet-base-v2",
    ):
        # 1. 加载faiss索引
        index_path = Path(index_dir) / "mathlib_informal.index"
        self.index = faiss.read_index(str(index_path))
        # 2. 加载sentence_transformer模型（使用本地缓存）
        self.model = SentenceTransformer(model_name)
        # 3. 加载dataset
        self.dataset = load_dataset("FrenzyMath/mathlib_informal_v4.16.0", split="train")

    def batch_retrieve(
        self,
        queries: List[str],
        top_k: int = 5,
    ) -> List[Dict]:
        total_results = []
        for query in queries:
            results = self.retrieve(query, top_k)
            total_results.extend(results)
        total_result = sorted(total_results, key=lambda x: x["score"], reverse=True)
        return total_result

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict]:
        query_embedding = self.model.encode([query], normalize_embeddings=True).astype("float32")
        scores, indices = self.index.search(query_embedding, top_k)
        results = []
        for score, index in zip(scores[0], indices[0]):
            record = self.dataset[int(index)]
            results.append(
                {
                    "name": record["name"],
                    "signature": record["signature"],
                    "type": record["type"],
                    # "value": record["value"],
                    "score": score,
                }
            )
        return results[:2]
