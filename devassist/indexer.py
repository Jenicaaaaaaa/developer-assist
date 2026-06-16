import os
import math
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from rank_bm25 import BM25Okapi
from devassist.config import CHROMA_DB_PATH, COLLECTION_NAME, SUPPORTED_EXTENSIONS
from sentence_transformers import CrossEncoder

# Load reranker model once at startup
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# Setup ChromaDB
embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_fn
)

# In-memory BM25 index — rebuilt on each index run
_bm25_index = None
_bm25_corpus = []
_bm25_metadata = []


def chunk_code(content, filepath, chunk_size=60, overlap=10):
    lines = content.splitlines()
    chunks = []

    for i in range(0, len(lines), chunk_size - overlap):
        chunk_lines = lines[i:i + chunk_size]
        chunk_text = "\n".join(chunk_lines)

        if chunk_text.strip():
            chunks.append({
                "text": chunk_text,
                "filepath": filepath,
                "start_line": i + 1,
                "end_line": i + len(chunk_lines)
            })

    return chunks


def index_codebase(repo_path: str):
    global _bm25_index, _bm25_corpus, _bm25_metadata

    all_chunks = []
    all_ids = []
    all_metadata = []
    indexed_files = 0

    print(f"\n🔍 Scanning: {repo_path}\n")

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in [
            ".git", "node_modules", "__pycache__",
            ".venv", "venv", "dist", "build"
        ]]

        for file in files:
            ext = os.path.splitext(file)[1]
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            filepath = os.path.join(root, file)

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                if not content.strip():
                    continue

                chunks = chunk_code(content, filepath)

                for idx, chunk in enumerate(chunks):
                    chunk_id = f"{filepath}::chunk_{idx}"
                    all_ids.append(chunk_id)
                    all_chunks.append(chunk["text"])
                    all_metadata.append({
                        "filepath": chunk["filepath"],
                        "start_line": chunk["start_line"],
                        "end_line": chunk["end_line"]
                    })

                indexed_files += 1
                print(f"  ✅ {filepath} ({len(chunks)} chunks)")

            except Exception as e:
                print(f"  ⚠️ Skipped {filepath}: {e}")

    # Store in ChromaDB
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        collection.add(
            documents=all_chunks[i:i + batch_size],
            ids=all_ids[i:i + batch_size],
            metadatas=all_metadata[i:i + batch_size]
        )

    # Build BM25 index in memory
    tokenized = [doc.lower().split() for doc in all_chunks]
    _bm25_index = BM25Okapi(tokenized)
    _bm25_corpus = all_chunks
    _bm25_metadata = all_metadata

    print(f"\n✅ Done. Indexed {indexed_files} files, {len(all_chunks)} chunks.")
    print(f"📊 BM25 index built with {len(tokenized)} documents.\n")


def _load_bm25_from_chroma():
    """Load all docs from ChromaDB into BM25 index if not already loaded"""
    global _bm25_index, _bm25_corpus, _bm25_metadata

    if _bm25_index is not None:
        return

    results = collection.get()
    if not results["documents"]:
        return

    _bm25_corpus = results["documents"]
    _bm25_metadata = results["metadatas"]
    tokenized = [doc.lower().split() for doc in _bm25_corpus]
    _bm25_index = BM25Okapi(tokenized)


def _reciprocal_rank_fusion(semantic_ids, bm25_ids, k=60):
    """
    Combine semantic and BM25 results using Reciprocal Rank Fusion.
    Higher score = more relevant.
    """
    scores = {}

    for rank, doc_id in enumerate(semantic_ids):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)

    for rank, doc_id in enumerate(bm25_ids):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def query_codebase(question: str, n_results: int = 5):
    """Hybrid retrieval with cross-encoder reranking"""

    # Ensure BM25 is loaded
    _load_bm25_from_chroma()

    # Fetch more candidates than needed for reranker to work with
    fetch_n = min(n_results * 4, 20)

    # --- Semantic search ---
    semantic_results = collection.query(
        query_texts=[question],
        n_results=fetch_n
    )
    semantic_docs = semantic_results["documents"][0]
    semantic_ids = semantic_results["ids"][0]
    semantic_meta = semantic_results["metadatas"][0]

    # --- BM25 search ---
    if _bm25_index is not None:
        tokenized_query = question.lower().split()
        bm25_scores = _bm25_index.get_scores(tokenized_query)

        bm25_top_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True
        )[:fetch_n]

        bm25_ids = [
            f"{_bm25_metadata[i]['filepath']}::chunk_{i}"
            for i in bm25_top_indices
        ]
        bm25_docs = [_bm25_corpus[i] for i in bm25_top_indices]
        bm25_meta = [_bm25_metadata[i] for i in bm25_top_indices]

        # --- Reciprocal Rank Fusion ---
        fused = _reciprocal_rank_fusion(semantic_ids, bm25_ids)

        # Build merged pool
        id_to_doc = {}
        id_to_meta = {}

        for doc, doc_id, meta in zip(semantic_docs, semantic_ids, semantic_meta):
            id_to_doc[doc_id] = doc
            id_to_meta[doc_id] = meta

        for doc, doc_id, meta in zip(bm25_docs, bm25_ids, bm25_meta):
            id_to_doc[doc_id] = doc
            id_to_meta[doc_id] = meta

        # Take top candidates from fusion for reranking
        candidate_ids = [doc_id for doc_id, _ in fused if doc_id in id_to_doc]
        candidate_docs = [id_to_doc[doc_id] for doc_id in candidate_ids]
        candidate_meta = [id_to_meta[doc_id] for doc_id in candidate_ids]

    else:
        # Fallback to semantic only
        candidate_ids = semantic_ids
        candidate_docs = semantic_docs
        candidate_meta = semantic_meta

    # --- Cross-Encoder Reranking ---
    if len(candidate_docs) > 0:
        pairs = [[question, doc] for doc in candidate_docs]
        rerank_scores = reranker.predict(pairs)

        # Sort by reranker score
        ranked = sorted(
            zip(rerank_scores, candidate_docs, candidate_ids, candidate_meta),
            key=lambda x: x[0],
            reverse=True
        )

        top = ranked[:n_results]
        final_docs = [r[1] for r in top]
        final_ids = [r[2] for r in top]
        final_meta = [r[3] for r in top]

        return {
            "documents": [final_docs],
            "metadatas": [final_meta],
            "ids": [final_ids]
        }

    return semantic_results
    """Hybrid retrieval: semantic + BM25 with reciprocal rank fusion"""

    # Ensure BM25 is loaded
    _load_bm25_from_chroma()

    # --- Semantic search via ChromaDB ---
    semantic_results = collection.query(
        query_texts=[question],
        n_results=min(n_results * 2, 20)
    )
    semantic_docs = semantic_results["documents"][0]
    semantic_ids = semantic_results["ids"][0]
    semantic_meta = semantic_results["metadatas"][0]

    # --- BM25 keyword search ---
    if _bm25_index is not None:
        tokenized_query = question.lower().split()
        bm25_scores = _bm25_index.get_scores(tokenized_query)

        # Get top N BM25 results
        top_n = min(n_results * 2, 20)
        bm25_top_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True
        )[:top_n]

        bm25_ids = [f"{_bm25_metadata[i]['filepath']}::chunk_{i}" for i in bm25_top_indices]
        bm25_docs = [_bm25_corpus[i] for i in bm25_top_indices]
        bm25_meta = [_bm25_metadata[i] for i in bm25_top_indices]

        # --- Reciprocal Rank Fusion ---
        fused = _reciprocal_rank_fusion(semantic_ids, bm25_ids)

        # Build final result from fused ranking
        id_to_doc = {}
        id_to_meta = {}

        for doc, doc_id, meta in zip(semantic_docs, semantic_ids, semantic_meta):
            id_to_doc[doc_id] = doc
            id_to_meta[doc_id] = meta

        for doc, doc_id, meta in zip(bm25_docs, bm25_ids, bm25_meta):
            id_to_doc[doc_id] = doc
            id_to_meta[doc_id] = meta

        final_ids = [doc_id for doc_id, _ in fused[:n_results]]
        final_docs = [id_to_doc[doc_id] for doc_id in final_ids if doc_id in id_to_doc]
        final_meta = [id_to_meta[doc_id] for doc_id in final_ids if doc_id in id_to_meta]

        return {
            "documents": [final_docs],
            "metadatas": [final_meta],
            "ids": [final_ids]
        }

    # Fallback to semantic only
    return semantic_results