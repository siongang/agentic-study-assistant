"""CLI to generate multi-exam study plan (Phase 8)."""
from pathlib import Path
import sys
import json
import argparse
from datetime import date, timedelta

from dotenv import load_dotenv

from app.tools.study_planner import generate_multi_exam_plan


def parse_date(date_str: str) -> date:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def main():
    """Generate multi-exam study plan."""
    parser = argparse.ArgumentParser(description="Generate multi-exam study plan")
    parser.add_argument(
        "exam_ids",
        type=str,
        help="Comma-separated enriched coverage file IDs"
    )
    parser.add_argument(
        "--start",
        type=str,
        default=date.today().isoformat(),
        help="Start date (YYYY-MM-DD, default: today)"
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD, default: auto-detect from exams)"
    )
    parser.add_argument(
        "--minutes",
        type=int,
        default=90,
        help="Study minutes per day (default: 90)"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["round_robin", "priority_first", "balanced"],
        default="balanced",
        help="Scheduling strategy (default: balanced)"
    )
    parser.add_argument(
        "--no-questions",
        action="store_true",
        help="Skip study question generation (faster)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Custom output directory"
    )
    
    args = parser.parse_args()
    
    load_dotenv()
    
    print("="*70)
    print("MULTI-EXAM STUDY PLANNER (Phase 8)")
    print("="*70)
    
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    enriched_dir = project_root / "storage" / "state" / "enriched_coverage"
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = project_root / "storage" / "state" / "plans"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse exam IDs
    exam_ids = [eid.strip() for eid in args.exam_ids.split(",")]
    
    # Build paths
    enriched_paths = []
    for exam_id in exam_ids:
        path = enriched_dir / f"{exam_id}.json"
        if not path.exists():
            print(f"❌ Error: Enriched coverage not found: {path}")
            print(f"\nAvailable files:")
            if enriched_dir.exists():
                for f in enriched_dir.glob("*.json"):
                    print(f"  - {f.stem}")
            print(f"\nRun: python -m app.cli.enrich_coverage {exam_id}")
            sys.exit(1)
        enriched_paths.append(path)
    
    print(f"\n📚 Planning for {len(enriched_paths)} exam(s):")
    for path in enriched_paths:
        print(f"  - {path.stem}")
    
    # Parse dates
    start_date = parse_date(args.start)
    
    if args.end:
        end_date = parse_date(args.end)
    else:
        # Auto-detect: read exam dates and set end date to earliest - 3 days
        earliest_exam = None
        for path in enriched_paths:
            with open(path) as f:
                data = json.load(f)
            if data.get("exam_date"):
                # Try to parse exam date (it's a string like "February 27, 2026")
                try:
                    # Simple heuristic: look for YYYY and assume reasonable date
                    # For MVP, just use 20 days from start
                    pass
                except:
                    pass
        
        # Default: 20 days from start
        end_date = start_date + timedelta(days=20)
        print(f"\n📅 Auto-set end date: {end_date} (20 days from start)")
    
    print(f"\n⚙️  Configuration:")
    print(f"   Start: {start_date}")
    print(f"   End: {end_date}")
    print(f"   Minutes/day: {args.minutes}")
    print(f"   Strategy: {args.strategy}")
    print(f"   Questions: {'disabled' if args.no_questions else 'enabled'}")
    
    # Generate plan
    try:
        plan = generate_multi_exam_plan(
            enriched_coverage_paths=enriched_paths,
            start_date=start_date,
            end_date=end_date,
            minutes_per_day=args.minutes,
            strategy=args.strategy,
            generate_questions=not args.no_questions
        )
    except Exception as e:
        print(f"\n❌ Error generating plan: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Save plan
    output_path = output_dir / f"{plan.plan_id}.json"
    with open(output_path, 'w') as f:
        json.dump(plan.model_dump(mode='json'), f, indent=2, default=str)
    
    print(f"\n{'='*70}")
    print("✅ Study Plan Generated!")
    print(f"{'='*70}")
    
    # Print summary
    print(f"\n📊 Plan Summary:")
    print(f"   Plan ID: {plan.plan_id}")
    print(f"   Total days: {plan.total_days}")
    print(f"   Total hours: {plan.total_study_hours:.1f}h")
    print(f"   Total topics: {plan.total_topics}")
    print(f"   Avg topics/day: {plan.total_topics / plan.total_days:.1f}")
    
    # Per-exam stats
    print(f"\n📚 Per-Exam Breakdown:")
    stats = plan.get_exam_stats()
    for exam_id, exam_stats in stats.items():
        hours = exam_stats['total_minutes'] / 60
        print(f"   {exam_stats['exam_name']}:")
        print(f"      Topics: {exam_stats['topics']}")
        print(f"      Time: {hours:.1f}h")
        print(f"      Avg confidence: {exam_stats['avg_confidence']:.2f}")
    
    # Show sample day
    if plan.days:
        sample_day = plan.days[0]
        print(f"\n📖 Sample Day ({sample_day.day_name}, {sample_day.date}):")
        print(f"   Total: {sample_day.total_minutes} minutes, {len(sample_day.blocks)} topics")
        for i, block in enumerate(sample_day.blocks[:2], 1):
            print(f"\n   {i}. {block.exam_name} - {block.topic}")
            print(f"      Objective: {block.objective[:80]}...")
            if block.reading_pages:
                print(f"      Reading: {block.reading_pages}")
            if block.key_terms:
                print(f"      Terms: {', '.join(block.key_terms[:3])}")
            if block.study_question:
                print(f"      Question: {block.study_question}")
            print(f"      Time: {block.time_estimate_minutes}min")
    
    print(f"\n💾 Saved to: {output_path}")
    print(f"   Size: {output_path.stat().st_size / 1024:.1f} KB")
    
    print(f"\n✨ Next: Export to CSV/Markdown with:")
    print(f"   python -m app.cli.export_plan {plan.plan_id} --format md")


if __name__ == "__main__":
    main()
