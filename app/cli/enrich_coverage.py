"""CLI to enrich exam coverage with textbook evidence (Phase 7)."""
from pathlib import Path
import sys
import json
import argparse

from dotenv import load_dotenv

from app.models.coverage import ExamCoverage
from app.tools.rag_scout import enrich_coverage


def main():
    """Enrich exam coverage with RAG Scout."""
    parser = argparse.ArgumentParser(description="Enrich exam coverage with textbook evidence")
    parser.add_argument("coverage_file_id", type=str, help="Coverage file ID (without .json)")
    parser.add_argument("--top-k", type=int, default=10, help="Chunks to retrieve per topic")
    parser.add_argument("--min-score", type=float, default=0.6, help="Minimum similarity score")
    parser.add_argument("--no-chapter-filter", action="store_true", help="Disable chapter filtering")
    parser.add_argument("--output-dir", type=str, help="Custom output directory")
    
    args = parser.parse_args()
    
    load_dotenv()
    
    print("="*70)
    print("RAG SCOUT - ENRICHING EXAM COVERAGE (Phase 7)")
    print("="*70)
    
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    coverage_path = project_root / "storage" / "state" / "coverage" / f"{args.coverage_file_id}.json"
    index_path = project_root / "storage" / "state" / "index" / "faiss.index"
    mapping_path = project_root / "storage" / "state" / "index" / "row_to_chunk_id.json"
    chunks_path = project_root / "storage" / "state" / "chunks" / "chunks.jsonl"
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = project_root / "storage" / "state" / "enriched_coverage"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.coverage_file_id}.json"
    
    # Check files exist
    if not coverage_path.exists():
        print(f"❌ Error: Coverage file not found: {coverage_path}")
        print(f"\nAvailable coverage files:")
        coverage_dir = coverage_path.parent
        if coverage_dir.exists():
            for f in coverage_dir.glob("*.json"):
                print(f"  - {f.stem}")
        sys.exit(1)
    
    if not index_path.exists():
        print(f"❌ Error: Index not found at {index_path}")
        print("Run: python -m app.cli.build_index first")
        sys.exit(1)
    
    # Load coverage
    print(f"\n[1/3] Loading coverage from {coverage_path.name}...", flush=True)
    with open(coverage_path) as f:
        coverage_data = json.load(f)
    
    coverage = ExamCoverage(**coverage_data)
    print(f"  ✓ Loaded: {coverage.exam_name}")
    print(f"  ✓ Chapters: {coverage.chapters}")
    total_topics = sum(len(ct.bullets) for ct in coverage.topics)
    print(f"  ✓ Total topics: {total_topics}")
    
    # Enrich coverage
    print(f"\n[2/3] Enriching coverage with RAG Scout...")
    print(f"  Settings:")
    print(f"    - Top-K: {args.top_k}")
    print(f"    - Min score: {args.min_score}")
    print(f"    - Chapter filter: {'enabled' if not args.no_chapter_filter else 'disabled'}")
    
    enriched = enrich_coverage(
        coverage=coverage,
        index_path=index_path,
        mapping_path=mapping_path,
        chunks_path=chunks_path,
        top_k=args.top_k,
        min_score=args.min_score,
        use_chapter_filter=not args.no_chapter_filter
    )
    
    # Save enriched coverage
    print(f"\n[3/3] Saving enriched coverage...", flush=True)
    with open(output_path, 'w') as f:
        json.dump(enriched.model_dump(mode='json'), f, indent=2, default=str)
    
    print(f"  ✓ Saved to: {output_path}")
    
    # Final summary
    print(f"\n{'='*70}")
    print("✅ Enrichment Complete!")
    print(f"{'='*70}")
    print(f"\nOutput file: {output_path}")
    print(f"Size: {output_path.stat().st_size / 1024:.1f} KB")
    
    # Show sample enriched topic
    if enriched.topics:
        print(f"\n📖 Sample enriched topic:")
        sample = enriched.topics[0]
        print(f"   Chapter: {sample.chapter}")
        print(f"   Objective: {sample.bullet[:80]}...")
        if sample.reading_pages.page_ranges:
            ranges_str = ", ".join(f"pp. {r[0]}-{r[1]}" if r[0] != r[1] else f"p. {r[0]}" 
                                   for r in sample.reading_pages.page_ranges)
            print(f"   Reading: {ranges_str}")
        if sample.practice_problems:
            print(f"   Problems: {len(sample.practice_problems)} found")
        if sample.key_terms:
            print(f"   Key terms: {', '.join(sample.key_terms[:3])}")
        print(f"   Confidence: {sample.confidence_score:.2f}")
    
    print(f"\n✨ Ready for Phase 8: Multi-Exam Planning!")


if __name__ == "__main__":
    main()
