"""CLI to export study plans to various formats (Phase 9)."""
from pathlib import Path
import sys
import json
import argparse

from app.models.plan import StudyPlan
from app.tools.plan_export import export_to_markdown, export_to_csv, export_to_json


def main():
    """Export study plan to readable format."""
    parser = argparse.ArgumentParser(description="Export study plan to CSV or Markdown")
    parser.add_argument("plan_id", type=str, help="Plan ID (UUID)")
    parser.add_argument(
        "--format",
        type=str,
        choices=["csv", "md", "markdown", "json"],
        default="md",
        help="Export format (default: md)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: auto-generate)"
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("STUDY PLAN EXPORT (Phase 9)")
    print("="*70)
    
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    plans_dir = project_root / "storage" / "state" / "plans"
    plan_path = plans_dir / f"{args.plan_id}.json"
    
    # Check plan exists
    if not plan_path.exists():
        print(f"\n❌ Error: Plan not found: {plan_path}")
        print(f"\nAvailable plans:")
        if plans_dir.exists():
            for f in plans_dir.glob("*.json"):
                print(f"  - {f.stem}")
        sys.exit(1)
    
    # Load plan
    print(f"\n[1/2] Loading plan {args.plan_id}...", flush=True)
    with open(plan_path) as f:
        plan_data = json.load(f)
    
    plan = StudyPlan(**plan_data)
    print(f"  ✓ Loaded: {len(plan.days)} days, {plan.total_topics} topics")
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Auto-generate filename
        format_ext = "md" if args.format in ["md", "markdown"] else args.format
        output_path = plans_dir / f"{args.plan_id}.{format_ext}"
    
    # Export
    print(f"\n[2/2] Exporting to {args.format.upper()}...", flush=True)
    
    try:
        if args.format in ["md", "markdown"]:
            export_to_markdown(plan, output_path)
        elif args.format == "csv":
            export_to_csv(plan, output_path)
        elif args.format == "json":
            export_to_json(plan, output_path)
        
        print(f"  ✓ Exported to: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Error exporting plan: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Summary
    print(f"\n{'='*70}")
    print("✅ Export Complete!")
    print(f"{'='*70}")
    print(f"\nOutput file: {output_path}")
    print(f"Size: {output_path.stat().st_size / 1024:.1f} KB")
    
    if args.format in ["md", "markdown"]:
        print(f"\n💡 Tip: Open with a markdown viewer for best experience")
        print(f"   Or view in terminal: cat {output_path}")
    elif args.format == "csv":
        print(f"\n💡 Tip: Open in Excel, Google Sheets, or any spreadsheet app")


if __name__ == "__main__":
    main()
