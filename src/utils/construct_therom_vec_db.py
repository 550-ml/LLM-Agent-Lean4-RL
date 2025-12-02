import argparse
import logging
from pathlib import Path

import faiss
from datasets import load_dataset
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_retrieve(
    query: str,
    index_path: str = "data/retriever/mathlib_informal.index",
    model_name: str = "all-mpnet-base-v2",
    top_k: int = 5,
):
    index = faiss.read_index(index_path)
    dataset = load_dataset("FrenzyMath/mathlib_informal_v4.16.0", split="train")

    # 2. model quert
    model = SentenceTransformer(model_name)
    query_embedding = model.encode([query], normalize_embeddings=True).astype("float32")

    # 3. 计算相似度
    scores, indices = index.search(query_embedding, top_k)

    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
        record = dataset[int(idx)]
        logger.info(f"[{i}] score={score:.4f} record={record}")


def build_theorem_index(
    output_dir,
    model_name,
    batch_size,
    use_local,
    local_path,
):
    """构建mathlib_informal 自然语言描述的向量索引

    Args:
        output_dir (_type_): _description_
        model_name (_type_): _description_
        batch_size (_type_): _description_
        use_local (_type_): _description_
        local_path (_type_): _description_
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. 加载mathlib_informal 数据集
    dataset = load_dataset("FrenzyMath/mathlib_informal_v4.16.0", split="train")
    logger.info(f"加载了 {len(dataset)} 条定理记录")
    logger.info(f"列名: {dataset.column_names}")

    # 2. 文本的search——text
    texts = dataset["informal_description"]

    # 3. 加载sentence_transformer 模型
    model = SentenceTransformer(model_name)
    dim = model.get_sentence_embedding_dimension()
    logger.info(f"向量维度: {dim}")

    # 4. 编码所有文本为向量
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    logger.info(f"编码完成，embeddings 形状: {embeddings.shape}")

    # 5. 构建FAISS索引
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    logger.info(f"FAISS 索引中共有 {index.ntotal} 条向量")

    # 6. 保存索引
    index_path = output_path / "mathlib_informal.index"
    faiss.write_index(index, str(index_path))
    logger.info(f"已保存 FAISS 索引到: {index_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="构建 Mathlib 定理向量索引")
    parser.add_argument("--output-dir", default="data/retriever", help="输出目录")
    parser.add_argument("--model", default="all-mpnet-base-v2", help="SentenceTransformer 模型")
    parser.add_argument("--batch-size", type=int, default=1800, help="编码批次大小")
    parser.add_argument("--local", action="store_true", help="使用本地 JSONL 文件")
    parser.add_argument("--local-path", default=None, help="本地 JSONL 文件路径")
    parser.add_argument("--test", action="store_true", help="构建后运行测试")
    parser.add_argument("--test-query", default="convex hull of finite set", help="测试查询")

    args = parser.parse_args()
    build_theorem_index(
        output_dir=args.output_dir,
        model_name=args.model,
        batch_size=args.batch_size,
        use_local=args.local,
        local_path=args.local_path,
    )

    test_retrieve(
        query=args.test_query, index_path=args.output_dir / "mathlib_informal.index", model_name=args.model, top_k=5
    )
