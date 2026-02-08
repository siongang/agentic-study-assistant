"""CLI to build FAISS index from chunks (Phase 6)."""
from pathlib import Path
import sys

from dotenv import load_dotenv

from app.tools.chunk_store import load_chunks_jsonl
from app.tools.embed import embed_texts
from app.tools.embedding_cache import get_or_compute_embeddings
from app.tools.faiss_index import build_faiss_index, build_chunk_mapping


def main():
    """Build FAISS index with embeddings."""
    print("="*60)
    print("BUILDING FAISS INDEX (Phase 6)")
    print("="*60)
    
    load_dotenv()
    
    project_root = Path(__file__).parent.parent.parent
    chunks_path = project_root / "storage" / "state" / "chunks" / "chunks.jsonl"
    cache_dir = project_root / "storage" / "state" / "embeddings"
    index_path = project_root / "storage" / "state" / "index" / "faiss.index"
    mapping_path = project_root / "storage" / "state" / "index" / "row_to_chunk_id.json"
    
    # Check chunks exist
    if not chunks_path.exists():
        print(f"❌ Error: Chunks not found at {chunks_path}")
        print("Run: python -m app.cli.chunk_textbooks first")
        sys.exit(1)
    
    print(f"\n[1/4] Loading chunks from {chunks_path}...", flush=True)
    chunks = load_chunks_jsonl(chunks_path)
    print(f"  ✓ Loaded {len(chunks)} chunks", flush=True)
    
    if not chunks:
        print("❌ No chunks found")
        sys.exit(1)
    
    print(f"\n[2/4] Computing embeddings (using cache)...", flush=True)
    print(f"  Model: gemini-embedding-001")
    print(f"  Cache dir: {cache_dir}", flush=True)
    
    # Define embedding function
    def embed_fn(texts):
        return embed_texts(
            texts,
            model="gemini-embedding-001",
            task_type="RETRIEVAL_DOCUMENT",
            batch_size=100
        )
    
    # Get or compute embeddings
    embeddings, stats = get_or_compute_embeddings(
        chunks=chunks,
        cache_dir=cache_dir,
        embed_function=embed_fn,
        show_progress=True
    )
    
    print(f"\n  📊 Embedding Stats:")
    print(f"    - Total: {stats['total']}")
    print(f"    - Cached: {stats['cached']}")
    print(f"    - Computed: {stats['computed']}")
    print(f"    - Shape: {embeddings.shape}", flush=True)
    
    print(f"\n[3/4] Building FAISS index...", flush=True)
    index = build_faiss_index(
        embeddings=embeddings,
        index_path=index_path,
        normalize=True  # For cosine similarity
    )
    
    print(f"\n[4/4] Building chunk mapping...", flush=True)
    mapping = build_chunk_mapping(
        chunks=chunks,
        mapping_path=mapping_path
    )
    
    print(f"\n{'='*60}")
    print("✅ Index Build Complete!")
    print(f"{'='*60}")
    print(f"\nFiles created:")
    print(f"  - FAISS index: {index_path}")
    print(f"  - Row mapping: {mapping_path}")
    print(f"  - Embeddings cache: {cache_dir}/ ({stats['total']} files)")
    print(f"\nIndex stats:")
    print(f"  - Vectors: {index.ntotal}")
    print(f"  - Dimensions: {embeddings.shape[1]}")
    print(f"  - Size: {index_path.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"\nReady for Phase 7: RAG Scout!")


if __name__ == "__main__":
    main()
