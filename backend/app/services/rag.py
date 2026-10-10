from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import List

import pymupdf as fitz
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.decomposition import TruncatedSVD
import numpy as np
import httpx

from app.config import (
    BASE_DIR,
    CHROMA_DIR,
    UPLOAD_DIR,
    CHUNK_MAX_CHARS,
    CHUNK_OVERLAP_CHARS,
    RETRIEVE_TOP_K,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
)

COLLECTION_NAME = "campus_rules"
EMBEDDING_DIM = 384
PIPELINE_PATH = CHROMA_DIR / "embedding_pipeline.pkl"


class LocalHashEmbedding(EmbeddingFunction):
    """无状态 HashingVectorizer + TruncatedSVD，不需要反复 fit"""

    def __init__(self):
        self._hasher = HashingVectorizer(
            analyzer="char",
            ngram_range=(2, 4),
            n_features=2**18,
            alternate_sign=False,
            norm=None,
        )
        self._svd: TruncatedSVD | None = None
        self._fitted = False

    def fit(self, documents: Documents):
        hashed = self._hasher.transform(documents)
        effective_dim = min(EMBEDDING_DIM, hashed.shape[1], max(2, hashed.shape[0] - 1))
        self._svd = TruncatedSVD(n_components=effective_dim, random_state=42)
        self._svd.fit(hashed)
        self._fitted = True
        self._save()
        print(f"[RAG] Embedding pipeline fitted (SVD dim={effective_dim}) ✓")

    def _save(self):
        try:
            import joblib
            joblib.dump(
                {"svd": self._svd, "fitted": self._fitted},
                str(PIPELINE_PATH),
            )
        except Exception:
            try:
                with open(PIPELINE_PATH, "wb") as f:
                    pickle.dump({"svd": self._svd, "fitted": self._fitted}, f)
            except Exception:
                pass

    def load(self):
        try:
            import joblib
            data = joblib.load(str(PIPELINE_PATH))
            self._svd = data["svd"]
            self._fitted = data.get("fitted", True)
            print("[RAG] Embedding pipeline loaded from disk ✓")
            return True
        except Exception:
            try:
                with open(PIPELINE_PATH, "rb") as f:
                    data = pickle.load(f)
                self._svd = data["svd"]
                self._fitted = data.get("fitted", True)
                print("[RAG] Embedding pipeline loaded from disk ✓")
                return True
            except Exception:
                return False

    def __call__(self, input: Documents) -> Embeddings:
        if not self._fitted or self._svd is None:
            raise RuntimeError("Embedding pipeline 未 fit 也未加载")
        hashed = self._hasher.transform(input)
        reduced = self._svd.transform(hashed)
        norms = np.linalg.norm(reduced, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        reduced = reduced / norms
        return reduced.tolist()


_embedding_fn: LocalHashEmbedding | None = None
_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None


def _get_embedding_fn() -> LocalHashEmbedding:
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = LocalHashEmbedding()
        if _embedding_fn.load():
            pass
    return _embedding_fn


def _get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is not None:
        return _collection

    emb_fn = _get_embedding_fn()
    _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        _collection = _client.get_collection(
            name=COLLECTION_NAME, embedding_function=emb_fn
        )
    except Exception:
        _collection = _client.create_collection(
            name=COLLECTION_NAME, embedding_function=emb_fn
        )
    return _collection


def _ensure_fitted():
    """从已存储的 chunks 重建 embedding 模型"""
    global _embedding_fn
    if _embedding_fn is not None and _embedding_fn._fitted:
        return

    collection = _get_collection()
    existing = collection.get(include=["documents"])
    if existing["documents"]:
        print(f"[RAG] 发现已有 {len(existing['documents'])} 个文本块，重新 fit embedding ...")
        emb_fn = _get_embedding_fn()
        emb_fn.fit(existing["documents"])
    else:
        emb_fn = _get_embedding_fn()
        emb_fn.fit(["请先上传文档以构建知识库。"])


def _chunk_text(text: str, max_chars: int, overlap: int) -> List[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if end >= len(text):
            break
    return chunks


def index_document(pdf_path: Path, original_name: str, size_bytes: int) -> int:
    collection = _get_collection()
    emb_fn = _get_embedding_fn()

    doc_hash = hashlib.md5(Path(pdf_path).read_bytes()).hexdigest()

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        raise RuntimeError(f"PDF 打开失败: {e}") from e

    total_pages = doc.page_count
    new_chunks = []
    new_metadatas = []
    new_ids = []

    existing_ids = set()
    try:
        all_existing = collection.get(where={"doc_hash": doc_hash}, include=[])
        existing_ids = set(all_existing["ids"])
    except Exception:
        pass

    for page_idx in range(total_pages):
        page = doc[page_idx]
        page_text = page.get_text("text")
        if not page_text.strip():
            continue

        chunks = _chunk_text(page_text, CHUNK_MAX_CHARS, CHUNK_OVERLAP_CHARS)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_hash}_p{page_idx + 1}_c{i}"
            if chunk_id in existing_ids:
                continue
            new_chunks.append(chunk)
            new_metadatas.append(
                {
                    "doc_name": original_name,
                    "doc_hash": doc_hash,
                    "page": page_idx + 1,
                    "chunk_index": i,
                }
            )
            new_ids.append(chunk_id)

    doc.close()

    if not new_chunks:
        print(f"[RAG] 文档 {original_name} 没有新增内容，跳过")
        return total_pages

    if not emb_fn._fitted:
        print(f"[RAG] 首次 fit embedding (用 {len(new_chunks)} 块) ...")
        emb_fn.fit(new_chunks)
    else:
        print(f"[RAG] 已有 embedding pipeline，直接索引 {len(new_chunks)} 块")

    collection.add(
        ids=new_ids,
        documents=new_chunks,
        metadatas=new_metadatas,
    )

    print(f"[RAG] 索引完成: {original_name} ({total_pages} 页, 新增 {len(new_chunks)} 块)")
    return total_pages


def count_documents() -> dict:
    try:
        collection = _get_collection()
        count = collection.count()
        all_data = collection.get(include=["metadatas"])
        doc_names = set()
        for m in all_data.get("metadatas", []):
            if m:
                doc_names.add(m.get("doc_name", ""))
        return {
            "total_chunks": count,
            "unique_documents": len([n for n in doc_names if n]),
            "collection": COLLECTION_NAME,
        }
    except Exception:
        return {"total_chunks": 0, "unique_documents": 0, "collection": COLLECTION_NAME}


def ask(question: str):
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY 环境变量")

    _ensure_fitted()

    collection = _get_collection()
    kb_status = count_documents()
    if kb_status["total_chunks"] == 0:
        return (
            "知识库还是空的哦！请先上传学校的规章制度 PDF，再来提问吧~",
            [],
        )

    emb_fn = _get_embedding_fn()
    if not emb_fn._fitted:
        return (
            "Embedding pipeline 未初始化，请先上传至少一个 PDF 文档。",
            [],
        )

    results = collection.query(
        query_texts=[question],
        n_results=min(RETRIEVE_TOP_K, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    retrieved_docs = results["documents"][0]
    retrieved_metas = results["metadatas"][0]
    retrieved_distances = results["distances"][0]

    if not retrieved_docs:
        return (
            "抱歉，没能从已上传的文档中检索到相关内容。请尝试换个方式提问，或者上传更多相关文档。",
            [],
        )

    context_parts = []
    source_items = []
    for idx, (doc, meta, dist) in enumerate(
        zip(retrieved_docs, retrieved_metas, retrieved_distances)
    ):
        page = meta.get("page", 0) if meta else 0
        doc_name = meta.get("doc_name", "未知文档") if meta else "未知文档"
        excerpt = doc[:200] + "..." if len(doc) > 200 else doc

        context_parts.append(
            f"--- 来源：{doc_name} 第 {page} 页 (相关度 {1 - dist:.2f}) ---\n{doc}"
        )
        source_items.append(
            {
                "page": page,
                "excerpt": excerpt,
                "doc_name": doc_name,
            }
        )

    context_str = "\n\n".join(context_parts)

    system_prompt = (
        "你是湖南科技职业学院的教务问答助手，专门回答学生关于学校规章制度的问题。\n"
        "你会收到从学校正式文件中检索到的若干段落（标有来源页码）。\n"
        "请严格依据这些检索内容回答，不要编造。如果检索内容不足以回答，请说明。\n"
        "回答格式要求：\n"
        "1. 先给出清晰的回答\n"
        "2. 最后单独一行注明「**参考来源**」，用项目符号列出每个来源的文件名和页码，例如：\n"
        "   - 《学生手册》第 12 页\n"
        "   - 《学籍管理规定》第 5 页"
    )

    user_prompt = (
        f"以下是从学校文件中检索到的相关段落：\n\n{context_str}\n\n"
        f"请根据以上内容回答学生的问题：{question}"
    )

    try:
        resp = httpx.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
                "stream": False,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        answer = data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        detail = e.response.text
        raise RuntimeError(f"DeepSeek API 报错 {e.response.status_code}: {detail}") from e
    except httpx.HTTPError as e:
        raise RuntimeError(f"DeepSeek API 网络错误: {e}") from e
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"DeepSeek API 返回格式异常: {e}") from e

    return answer, source_items


def reset_knowledge_base():
    """清空 ChromaDB 知识库（调试用）"""
    global _collection, _client, _embedding_fn
    if _client is not None:
        try:
            _client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        _client = None
        _collection = None
        _embedding_fn = None
    import shutil
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR, ignore_errors=True)
        CHROMA_DIR.mkdir(exist_ok=True)
    print("[RAG] 知识库已清空")