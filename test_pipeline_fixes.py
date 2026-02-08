#!/usr/bin/env python3
"""Test script to verify pipeline fixes.

This script helps verify:
1. Classification bug is fixed (doc_type gets updated)
2. Caching works (no reprocessing when status='processed')
3. Status transitions work correctly
"""
import json
from pathlib import Path

def test_manifest_classification():
    """Check if manifest has proper doc_types after fixes."""
    manifest_path = Path("storage/state/manifest.json")
    
    if not manifest_path.exists():
        print("❌ Manifest not found")
        return False
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    print("\n📋 Manifest Status Check:")
    print("-" * 60)
    
    unknown_count = 0
    for file in manifest["files"]:
        status = file["status"]
        doc_type = file["doc_type"]
        filename = file["filename"]
        
        if doc_type == "unknown":
            unknown_count += 1
            print(f"⚠️  {filename[:50]:<50} | {doc_type:<15} | {status}")
        else:
            print(f"✅ {filename[:50]:<50} | {doc_type:<15} | {status}")
    
    print("-" * 60)
    if unknown_count > 0:
        print(f"\n⚠️  Found {unknown_count} files with doc_type='unknown'")
        print("   Run classify_document() on these files to fix.")
    else:
        print("\n✅ All files classified!")
    
    return unknown_count == 0


def check_caching_artifacts():
    """Verify extracted text and metadata exist."""
    state_dir = Path("storage/state")
    
    extracted_text_dir = state_dir / "extracted_text"
    toc_dir = state_dir / "textbook_metadata"
    
    extracted_count = len(list(extracted_text_dir.glob("*.json"))) if extracted_text_dir.exists() else 0
    toc_count = len(list(toc_dir.glob("*.json"))) if toc_dir.exists() else 0
    
    print("\n📦 Cached Artifacts:")
    print("-" * 60)
    print(f"Extracted text files: {extracted_count}")
    print(f"TOC metadata files:   {toc_count}")
    print("-" * 60)
    
    return extracted_count > 0


def suggest_test_steps():
    """Print manual testing steps."""
    print("\n🧪 Manual Testing Steps:")
    print("-" * 60)
    print("""
1. Start the ADK server:
   $ cd /home/sion/code/study-agent
   $ python -m adk dev --app app.agent

2. Open the ADK web UI and test the ingest agent:
   a. Say: "Process all files"
   b. Verify: Files with status='processed' are skipped (cached)
   c. Verify: Files with doc_type='unknown' get classified
   d. Check logs for "✓ Using cached..." messages

3. Check manifest.json after processing:
   $ python test_pipeline_fixes.py

4. Verify no redundant processing in logs:
   - Look for "Already extracted (cached)" messages
   - Look for "✓ Using cached TOC" messages
   - Ensure no duplicate extraction/TOC operations

Expected Behavior:
✅ classify_document() should update doc_type without errors
✅ Tools should skip files with status='processed'
✅ Tools should show "cached" messages in logs
✅ No redundant text extraction or TOC processing
    """)
    print("-" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("  Pipeline Fixes Verification Script")
    print("=" * 60)
    
    test_manifest_classification()
    check_caching_artifacts()
    suggest_test_steps()
    
    print("\n✅ Verification complete!")
    print("\nNext: Run the manual testing steps above to verify live behavior.")
