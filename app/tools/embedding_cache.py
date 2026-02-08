"""Simple file-based embedding cache to avoid redundant API calls."""
from pathlib import Path
import numpy as np
import hashlib


def get_cache_path(chunk_id: str, cache_dir: Path) -> Path:
    """
    Get cache file path for a chunk.
    
    Args:
        chunk_id: Unique chunk identifier
        cache_dir: Directory for embedding cache
        
    Returns:
        Path to cache file
    """
    return cache_dir / f"{chunk_id}.npy"


def get_text_hash(text: str) -> str:
    """Get hash of text content for change detection."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:8]


def load_cached_embedding(
    chunk_id: str,
    text: str,
    cache_dir: Path
) -> tuple[np.ndarray | None, bool]:
    """
    Load embedding from cache if it exists and text hasn't changed.
    
    Args:
        chunk_id: Unique chunk identifier
        text: Current text content
        cache_dir: Directory for embedding cache
        
    Returns:
        Tuple of (embedding array or None, cache_valid boolean)
    """
    cache_path = get_cache_path(chunk_id, cache_dir)
    
    if not cache_path.exists():
        return None, False
    
    try:
        # Load cached embedding
        embedding = np.load(cache_path)
        
        # Check metadata file for text hash
        meta_path = cache_path.with_suffix('.meta')
        if meta_path.exists():
            cached_hash = meta_path.read_text().strip()
            current_hash = get_text_hash(text)
            
            if cached_hash == current_hash:
                # Text unchanged - cache is valid
                return embedding, True
            else:
                # Text changed - cache is stale
                return None, False
        else:
            # No metadata - assume cache is valid (backward compat)
            return embedding, True
            
    except Exception as e:
        print(f"Warning: Failed to load cached embedding for {chunk_id}: {e}")
        return None, False


def save_embedding_to_cache(
    chunk_id: str,
    text: str,
    embedding: np.ndarray,
    cache_dir: Path
) -> None:
    """
    Save embedding to cache with text hash for change detection.
    
    Args:
        chunk_id: Unique chunk identifier
        text: Text content
        embedding: Embedding array
        cache_dir: Directory for embedding cache
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    cache_path = get_cache_path(chunk_id, cache_dir)
    
    # Save embedding
    np.save(cache_path, embedding)
    
    # Save text hash for change detection
    meta_path = cache_path.with_suffix('.meta')
    text_hash = get_text_hash(text)
    meta_path.write_text(text_hash)


def get_or_compute_embeddings(
    chunks: list,
    cache_dir: Path,
    embed_function: callable,
    show_progress: bool = True
) -> tuple[np.ndarray, dict]:
    """
    Get embeddings from cache or compute them.
    
    Args:
        chunks: List of Chunk objects
        cache_dir: Directory for embedding cache
        embed_function: Function to compute embeddings for a list of texts
        show_progress: Whether to show progress messages
        
    Returns:
        Tuple of (embeddings array, stats dict)
    """
    embeddings_list = []
    texts_to_embed = []
    indices_to_embed = []
    
    stats = {
        "total": len(chunks),
        "cached": 0,
        "computed": 0
    }
    
    if show_progress:
        print(f"  Checking cache for {len(chunks)} chunks...", flush=True)
    
    # Check cache for each chunk
    for idx, chunk in enumerate(chunks):
        cached_embedding, is_valid = load_cached_embedding(
            chunk.chunk_id,
            chunk.text,
            cache_dir
        )
        
        if is_valid and cached_embedding is not None:
            # Use cached embedding
            embeddings_list.append(cached_embedding)
            stats["cached"] += 1
        else:
            # Need to compute
            embeddings_list.append(None)  # Placeholder
            texts_to_embed.append(chunk.text)
            indices_to_embed.append(idx)
    
    if show_progress:
        print(f"  ✓ Found {stats['cached']} cached embeddings, computing {len(texts_to_embed)} new ones", flush=True)
    
    # Compute missing embeddings
    if texts_to_embed:
        if show_progress:
            print(f"  Computing {len(texts_to_embed)} embeddings...", flush=True)
        
        new_embeddings = embed_function(texts_to_embed)
        stats["computed"] = len(texts_to_embed)
        
        # Insert computed embeddings and save to cache
        for i, idx in enumerate(indices_to_embed):
            embedding = new_embeddings[i]
            embeddings_list[idx] = embedding
            
            # Save to cache
            chunk = chunks[idx]
            save_embedding_to_cache(
                chunk.chunk_id,
                chunk.text,
                embedding,
                cache_dir
            )
    
    # Convert to numpy array
    embeddings_array = np.array(embeddings_list, dtype=np.float32)
    
    if show_progress:
        print(f"  ✓ Total: {stats['cached']} cached + {stats['computed']} computed = {stats['total']} embeddings", flush=True)
    
    return embeddings_array, stats
