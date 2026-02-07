"""Orchestrator for document classification with manifest integration (Phase 3)."""
from pathlib import Path
from typing import Optional

from app.models.manifest import Manifest
from app.models.extracted_text import ExtractedText
from app.tools.manifest_io import load_manifest, save_manifest
from app.tools.text_extraction import load_extracted_text
from app.tools.doc_classify import classify_document


def classify_all_processed(
    manifest_path: Path,
    extracted_text_dir: Path,
    progress_callback: Optional[callable] = None
) -> dict:
    """
    Classify all documents that have been processed (extracted).
    
    Updates manifest with:
    - doc_type
    - doc_confidence
    - doc_reasoning
    
    Args:
        manifest_path: Path to manifest.json
        extracted_text_dir: Directory with extracted text files
        progress_callback: Optional callback(file_entry) for progress reporting
    
    Returns:
        dict with stats: {"classified": int, "skipped": int, "failed": int}
    """
    # Load manifest
    manifest = load_manifest(manifest_path)
    if manifest is None:
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    # Track stats
    stats = {"classified": 0, "skipped": 0, "failed": 0}
    
    # Process each file that has been extracted
    for file_entry in manifest.files:
        if file_entry.status != "processed":
            stats["skipped"] += 1
            continue
        
        # Skip if already classified (not "unknown")
        if file_entry.doc_type != "unknown":
            stats["skipped"] += 1
            continue
        
        # Report progress
        if progress_callback:
            progress_callback(file_entry)
        
        # Load extracted text
        extracted = load_extracted_text(file_entry.file_id, extracted_text_dir)
        if extracted is None:
            stats["failed"] += 1
            continue
        
        # Classify using LLM
        try:
            result = classify_document(
                first_page=extracted.first_page,
                filename=file_entry.filename,
                full_text_sample=extracted.full_text[:2000] if len(extracted.full_text) > 2000 else ""
            )
            
            # Update manifest entry
            file_entry.doc_type = result["doc_type"]
            file_entry.doc_confidence = result["confidence"]
            file_entry.doc_reasoning = result["reasoning"]
            
            stats["classified"] += 1
            
        except Exception as e:
            stats["failed"] += 1
            file_entry.doc_reasoning = f"Classification error: {str(e)}"
    
    # Save updated manifest
    save_manifest(manifest, manifest_path)
    
    return stats
