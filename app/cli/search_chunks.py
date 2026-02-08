"""CLI to search chunks using FAISS index."""
from pathlib import Path
import sys
import argparse

from dotenv import load_dotenv

from app.tools.embed import embed_query
from app.tools.faiss_index import (
    load_faiss_index,
    load_chunk_mapping,
    search_index,
    retrieve_chunks_with_text
)


def main():
    """Search chunks with semantic similarity."""
    parser = argparse.ArgumentParser(description="Search textbook chunks semantically")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--chapter", type=int, help="Filter by chapter number")
    parser.add_argument("--min-score", type=float, help="Minimum similarity score")
    parser.add_argument("--show-text", action="store_true", help="Show full chunk text")
    
    args = parser.parse_args()
    
    load_dotenv()
    
    project_root = Path(__file__).parent.parent.parent
    index_path = project_root / "storage" / "state" / "index" / "faiss.index"
    mapping_path = project_root / "storage" / "state" / "index" / "row_to_chunk_id.json"
    chunks_path = project_root / "storage" / "state" / "chunks" / "chunks.jsonl"
    
    # Check index exists
    if not index_path.exists():
        print(f"❌ Error: Index not found at {index_path}")
        print("Run: python -m app.cli.build_index first")
        sys.exit(1)
    
    print(f"🔍 Searching for: \"{args.query}\"")
    if args.chapter:
        print(f"   Filtering: Chapter {args.chapter}")
    if args.min_score:
        print(f"   Min score: {args.min_score}")
    print()
    
    # Load index and mapping
    print("Loading index...", flush=True)
    index = load_faiss_index(index_path)
    mapping = load_chunk_mapping(mapping_path)
    print(f"✓ Loaded index with {index.ntotal} vectors\n")
    
    # Embed query
    print("Embedding query...", flush=True)
    query_embedding = embed_query(args.query)
    print(f"✓ Embedded query\n")
    
    # Build filters
    filters = {}
    if args.chapter:
        filters["chapter_number"] = args.chapter
    if args.min_score:
        filters["min_score"] = args.min_score
    
    # Search
    print(f"Searching (top-k={args.top_k})...", flush=True)
    results = search_index(
        query_embedding=query_embedding,
        index=index,
        mapping=mapping,
        chunks_path=chunks_path,
        top_k=args.top_k,
        filters=filters if filters else None
    )
    
    if not results:
        print("❌ No results found")
        sys.exit(0)
    
    print(f"✓ Found {len(results)} results\n")
    print("="*70)
    
    # Add text if requested
    if args.show_text:
        results = retrieve_chunks_with_text(results, chunks_path)
    
    # Display results
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']:.4f}")
        print(f"   File: {result['filename'][:60]}...")
        print(f"   Pages: {result['page_start']}", end="")
        if result['page_end'] != result['page_start']:
            print(f"-{result['page_end']}", end="")
        print()
        
        if result.get('chapter_number'):
            print(f"   Chapter: {result['chapter_number']} - {result.get('chapter_title', 'N/A')[:50]}")
        
        print(f"   Chunk ID: {result['chunk_id']}")
        print(f"   Tokens: {result['token_count']}")
        
        if args.show_text and 'text' in result:
            text_preview = result['text'][:200]
            print(f"\n   Text: \"{text_preview}...\"")
        
        print("-"*70)


if __name__ == "__main__":
    main()
