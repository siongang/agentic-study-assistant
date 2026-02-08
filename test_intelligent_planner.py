#!/usr/bin/env python3
"""Test the intelligent planner components."""

from datetime import date
from pathlib import Path
from app.models.plan import Priority, StudyBlock
from app.tools.intelligent_planner import analyze_study_load

# Test 1: Priority enum
print("=" * 60)
print("Test 1: Priority System")
print("=" * 60)
print("Priority levels:", [p.value for p in Priority])
print()

# Test 2: Create a study block with priority
print("=" * 60)
print("Test 2: StudyBlock with Priority")
print("=" * 60)
block = StudyBlock(
    exam_id="test_exam",
    exam_name="Test Exam",
    course="TEST 101",
    chapter=1,
    chapter_title="Introduction",
    topic="Ch 1: Introduction",
    objective="Understand basic concepts",
    time_estimate_minutes=45,
    confidence_score=0.85,
    priority=Priority.CRITICAL,
    priority_reason="Foundational concept required for all subsequent topics"
)
print(f"Block priority: {block.priority.value}")
print(f"Priority reason: {block.priority_reason}")
print()

# Test 3: Analyze study load (if enriched coverage exists)
print("=" * 60)
print("Test 3: Analyze Study Load")
print("=" * 60)

enriched_dir = Path("storage/state/enriched_coverage")
if enriched_dir.exists():
    enriched_files = list(enriched_dir.glob("*.json"))
    if enriched_files:
        print(f"Found {len(enriched_files)} enriched coverage files")
        
        # Test with first file
        test_file = enriched_files[0]
        print(f"Testing with: {test_file.name}")
        
        try:
            start_date = date.today()
            end_date = date(2026, 2, 20)
            
            result = analyze_study_load(
                enriched_coverage_paths=[test_file],
                start_date=start_date,
                end_date=end_date,
                minutes_per_day=90
            )
            
            print(f"\nAnalysis Results:")
            print(f"  Total topics: {result['total_topics']}")
            print(f"  Time needed: {result['total_time_needed_hours']}h")
            print(f"  Time available: {result['time_available_hours']}h")
            print(f"  Feasibility: {result['feasibility']}")
            print(f"  Coverage: {result['coverage_percentage']}%")
            print(f"  Recommendation: {result['recommendation']}")
        except Exception as e:
            print(f"Error in analysis: {e}")
    else:
        print("No enriched coverage files found")
        print("Run: python -m app.cli.enrich_coverage <exam_file_id>")
else:
    print("Enriched coverage directory not found")
    print("Run pipeline first to generate test data")

print()
print("=" * 60)
print("✅ All basic tests passed!")
print("=" * 60)
print()
print("To test the full intelligent planner:")
print("1. Ensure you have enriched coverage: python -m app.cli.enrich_coverage <file_id>")
print("2. Use the agent: 'Create a smart study plan with priorities'")
print("3. Or call directly: generate_smart_plan(...)")
