"""Embedding utilities using modern google-genai SDK."""
import os
import time
from typing import List
import numpy as np
from google import genai
from google.genai import types


def get_genai_client():
    """Get authenticated Google GenAI client."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment")
    
    client = genai.Client(api_key=api_key)
    return client


def embed_texts(
    texts: List[str],
    model: str = "gemini-embedding-001",
    task_type: str = "RETRIEVAL_DOCUMENT",
    batch_size: int = 100,
    max_retries: int = 3
) -> np.ndarray:
    """
    Embed a list of texts using Google's embedding-001 model.
    
    Args:
        texts: List of text strings to embed
        model: Model name (default: models/embedding-001)
        task_type: Task type for embeddings (RETRIEVAL_DOCUMENT or RETRIEVAL_QUERY)
        batch_size: Maximum texts per batch (default 100)
        max_retries: Maximum retry attempts for rate limits
        
    Returns:
        numpy array of shape (len(texts), embedding_dim)
    """
    client = get_genai_client()
    
    all_embeddings = []
    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        print(f"  Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)...", flush=True)
        
        # Retry logic for rate limits
        for attempt in range(max_retries):
            try:
                # Create embedding config (without model - that goes in embed_content)
                config = types.EmbedContentConfig(
                    task_type=task_type
                )
                
                # Embed the batch
                response = client.models.embed_content(
                    model=model,
                    contents=batch,
                    config=config
                )
                
                # Extract embeddings
                batch_embeddings = [emb.values for emb in response.embeddings]
                all_embeddings.extend(batch_embeddings)
                
                # Success - break retry loop
                break
                
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    # Rate limit - wait and retry
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"    ⚠ Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...", flush=True)
                    time.sleep(wait_time)
                    
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed after {max_retries} retries: {e}")
                else:
                    # Other error - raise immediately
                    raise Exception(f"Embedding error: {e}")
        
        # Small delay between batches to avoid rate limits
        if i + batch_size < len(texts):
            time.sleep(0.1)
    
    # Convert to numpy array
    embeddings_array = np.array(all_embeddings, dtype=np.float32)
    print(f"  ✓ Embedded {len(texts)} texts, shape: {embeddings_array.shape}", flush=True)
    
    return embeddings_array


def embed_query(
    query: str,
    model: str = "gemini-embedding-001"
) -> np.ndarray:
    """
    Embed a single query text for retrieval.
    
    Args:
        query: Query text to embed
        model: Model name (default: models/embedding-001)
        
    Returns:
        numpy array of shape (embedding_dim,)
    """
    client = get_genai_client()
    
    config = types.EmbedContentConfig(
        task_type="RETRIEVAL_QUERY"
    )
    
    response = client.models.embed_content(
        model=model,
        contents=[query],
        config=config
    )
    
    embedding = np.array(response.embeddings[0].values, dtype=np.float32)
    return embedding
