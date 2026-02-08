"""FAISS index building and search with chapter-aware filtering."""
from pathlib import Path
import json
import numpy as np
import faiss
from typing import List, Optional, Dict, Any

from app.models.chunks import Chunk
from app.tools.chunk_store import load_chunks_jsonl


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """
    Normalize vectors to unit length for cosine similarity.
    
    Args:
        vectors: Array of shape (n, dim)
        
    Returns:
        Normalized vectors
    """
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    # Avoid division by zero
    norms = np.where(norms == 0, 1, norms)
    return vectors / norms


def build_faiss_index(
    embeddings: np.ndarray,
    index_path: Path,
    normalize: bool = True
) -> faiss.Index:
    """
    Build FAISS index for semantic search.
    
    Uses IndexFlatIP (inner product) with normalized vectors for cosine similarity.
    
    Args:
        embeddings: Array of shape (n_chunks, embedding_dim)
        index_path: Path to save index
        normalize: Whether to normalize vectors (default True for cosine similarity)
        
    Returns:
        Built FAISS index
    """
    print(f"  Building FAISS index...", flush=True)
    
    # Normalize for cosine similarity
    if normalize:
        embeddings = normalize_vectors(embeddings)
    
    # Get embedding dimension
    dim = embeddings.shape[1]
    
    # Create flat IP index (inner product - equivalent to cosine with normalized vectors)
    index = faiss.IndexFlatIP(dim)
    
    # Add vectors to index
    index.add(embeddings)
    
    print(f"  ✓ Built FAISS index: {index.ntotal} vectors, {dim} dimensions", flush=True)
    
    # Save index
    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    print(f"  ✓ Saved index to {index_path}", flush=True)
    
    return index


def build_chunk_mapping(
    chunks: List[Chunk],
    mapping_path: Path
) -> Dict[int, str]:
    """
    Build mapping from FAISS row index to chunk_id.
    
    Args:
        chunks: List of Chunk objects (in same order as embeddings)
        mapping_path: Path to save mapping JSON
        
    Returns:
        Dictionary mapping row index to chunk_id
    """
    mapping = {}
    for idx, chunk in enumerate(chunks):
        mapping[idx] = {
            "chunk_id": chunk.chunk_id,
            "file_id": chunk.file_id,
            "filename": chunk.filename,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "chapter_number": chunk.chapter_number,
            "chapter_title": chunk.chapter_title,
            "token_count": chunk.token_count
        }
    
    # Save mapping
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_path.write_text(json.dumps(mapping, indent=2))
    print(f"  ✓ Saved row→chunk mapping to {mapping_path}", flush=True)
    
    return mapping


def load_faiss_index(index_path: Path) -> faiss.Index:
    """Load FAISS index from disk."""
    if not index_path.exists():
        raise FileNotFoundError(f"Index not found: {index_path}")
    
    index = faiss.read_index(str(index_path))
    return index


def load_chunk_mapping(mapping_path: Path) -> Dict[int, Dict]:
    """Load row→chunk mapping from disk."""
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping not found: {mapping_path}")
    
    mapping = json.loads(mapping_path.read_text())
    # Convert string keys to integers
    return {int(k): v for k, v in mapping.items()}


def search_index(
    query_embedding: np.ndarray,
    index: faiss.Index,
    mapping: Dict[int, Dict],
    chunks_path: Path,
    top_k: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    normalize: bool = True
) -> List[Dict]:
    """
    Search FAISS index with optional chapter filtering.
    
    Args:
        query_embedding: Query vector of shape (embedding_dim,)
        index: FAISS index
        mapping: Row→chunk mapping
        chunks_path: Path to chunks JSONL file
        top_k: Number of results to return
        filters: Optional filters dict with keys:
            - chapter_number: int or list of ints
            - file_id: str
            - min_score: float (minimum similarity score)
        normalize: Whether to normalize query vector
        
    Returns:
        List of dicts with chunk info and scores
    """
    # Normalize query
    if normalize:
        query_embedding = normalize_vectors(query_embedding.reshape(1, -1))[0]
    
    # Search with larger k for post-filtering
    search_k = top_k * 3 if filters else top_k
    scores, indices = index.search(
        query_embedding.reshape(1, -1).astype(np.float32),
        search_k
    )
    
    # Get results
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:  # FAISS returns -1 for empty results
            continue
        
        # Get chunk metadata from mapping
        chunk_meta = mapping.get(int(idx))
        if not chunk_meta:
            continue
        
        # Apply filters
        if filters:
            # Chapter filter
            if "chapter_number" in filters:
                chapter_filter = filters["chapter_number"]
                if isinstance(chapter_filter, (list, tuple)):
                    if chunk_meta.get("chapter_number") not in chapter_filter:
                        continue
                else:
                    if chunk_meta.get("chapter_number") != chapter_filter:
                        continue
            
            # File filter
            if "file_id" in filters:
                if chunk_meta.get("file_id") != filters["file_id"]:
                    continue
            
            # Score filter
            if "min_score" in filters:
                if float(score) < filters["min_score"]:
                    continue
        
        result = {
            "chunk_id": chunk_meta["chunk_id"],
            "score": float(score),
            "file_id": chunk_meta["file_id"],
            "filename": chunk_meta["filename"],
            "page_start": chunk_meta["page_start"],
            "page_end": chunk_meta["page_end"],
            "chapter_number": chunk_meta.get("chapter_number"),
            "chapter_title": chunk_meta.get("chapter_title"),
            "token_count": chunk_meta["token_count"]
        }
        results.append(result)
        
        # Stop if we have enough results
        if len(results) >= top_k:
            break
    
    return results


def retrieve_chunks_with_text(
    results: List[Dict],
    chunks_path: Path
) -> List[Dict]:
    """
    Add full text to search results.
    
    Args:
        results: List of search results from search_index()
        chunks_path: Path to chunks JSONL file
        
    Returns:
        List of results with 'text' field added
    """
    # Load all chunks
    chunks = load_chunks_jsonl(chunks_path)
    chunk_dict = {chunk.chunk_id: chunk for chunk in chunks}
    
    # Add text to results
    for result in results:
        chunk = chunk_dict.get(result["chunk_id"])
        if chunk:
            result["text"] = chunk.text
    
    return results
