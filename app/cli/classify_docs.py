"""CLI to classify documents using LLM (Phase 3)."""
from pathlib import Path
import sys

from dotenv import load_dotenv
from tqdm import tqdm

from app.tools.doc_classification import classify_all_processed
from app.tools.manifest_io import load_manifest


def main():
    """Classify all processed documents and show progress."""
    # Load environment variables (for GOOGLE_API_KEY)
    load_dotenv()
    
    project_root = Path(__file__).parent.parent.parent
    manifest_path = project_root / "storage" / "state" / "manifest.json"
    extracted_text_dir = project_root / "storage" / "state" / "extracted_text"
    
    if not manifest_path.exists():
        print("Error: manifest.json not found. Run update_manifest first.")
        sys.exit(1)
    
    manifest = load_manifest(manifest_path)
    if manifest is None:
        print("Error: Failed to load manifest")
        sys.exit(1)
    
    needs_classification = [
        f for f in manifest.files 
        if f.status == "processed" and f.doc_type == "unknown"
    ]
    
    if not needs_classification:
        print("No files need classification.")
        print("\nCurrent classifications:")
        for file in manifest.files:
            if file.status == "processed":
                conf = f"({file.doc_confidence:.2f})" if file.doc_confidence else ""
                print(f"  [{file.doc_type:15}] {conf:8} {file.filename}")
        return
    
    print(f"Classifying {len(needs_classification)} documents using Gemini Flash...\n")
    
    pbar = tqdm(total=len(needs_classification), desc="Classifying", unit="doc")
    
    def progress_callback(file_entry):
        pbar.set_postfix_str(file_entry.filename[:40])
        pbar.update(1)
    
    try:
        stats = classify_all_processed(
            manifest_path=manifest_path,
            extracted_text_dir=extracted_text_dir,
            progress_callback=progress_callback
        )
        
        pbar.close()
        
        print("\n=== Classification Summary ===")
        print(f"Successfully classified: {stats['classified']}")
        print(f"Failed:                  {stats['failed']}")
        print(f"Skipped:                 {stats['skipped']}")
        
        manifest = load_manifest(manifest_path)
        print("\n=== Document Types ===")
        for file in manifest.files:
            if file.status == "processed":
                conf = f"({file.doc_confidence:.2f})" if file.doc_confidence else ""
                print(f"  [{file.doc_type:15}] {conf:8} {file.filename}")
                if file.doc_reasoning:
                    print(f"    -> {file.doc_reasoning[:100]}")
        
    except Exception as e:
        pbar.close()
        print(f"\nError during classification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
