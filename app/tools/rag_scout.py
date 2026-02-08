"""RAG Scout: Enrich exam coverage with textbook evidence (Phase 7).

This tool bridges abstract learning objectives to concrete textbook resources by:
1. Querying FAISS for relevant chunks (with chapter filtering)
2. Extracting reading pages, practice problems, and key terms
3. Calculating confidence scores for each topic
"""
from pathlib import Path
import re
import json
from collections import Counter
from typing import Optional

import numpy as np

from app.models.coverage import ExamCoverage
from app.models.enriched_coverage import (
    EnrichedCoverage,
    EnrichedTopic,
    ReadingPages,
    PracticeProblem
)
from app.models.chunks import Chunk
from app.tools.chunk_store import load_chunks_jsonl
from app.tools.faiss_index import (
    load_faiss_index,
    load_chunk_mapping,
    search_index
)
from app.tools.embed import embed_query


def consolidate_page_ranges(pages: list[int], gap_tolerance: int = 3) -> list[list[int]]:
    """
    Consolidate page numbers into ranges.
    
    Args:
        pages: List of page numbers
        gap_tolerance: Max gap to consider pages consecutive
        
    Returns:
        List of [start, end] ranges
        
    Example:
        [1, 2, 3, 7, 8, 15] -> [[1, 3], [7, 8], [15, 15]]
    """
    if not pages:
        return []
    
    pages = sorted(set(pages))  # Remove duplicates and sort
    ranges = []
    start = pages[0]
    end = pages[0]
    
    for page in pages[1:]:
        if page - end <= gap_tolerance:
            # Extend current range
            end = page
        else:
            # Start new range
            ranges.append([start, end])
            start = page
            end = page
    
    # Add final range
    ranges.append([start, end])
    
    return ranges


def extract_practice_problems(
    chunks: list[Chunk],
    max_problems: int = 5
) -> list[PracticeProblem]:
    """
    Extract practice problem references from chunks.
    
    Args:
        chunks: List of chunks to search
        max_problems: Maximum number of problems to return
        
    Returns:
        List of PracticeProblem objects
    """
    problems = []
    problem_patterns = [
        r'Problem\s+\d+\.?\d*',
        r'Exercise\s+\d+\.?\d*',
        r'Question\s+\d+\.?\d*',
        r'Challenge\s+\d+\.\d+\.\d+',
        r'Practice\s+\d+\.?\d*',
    ]
    
    for chunk in chunks:
        # Search for problem patterns in text
        for pattern in problem_patterns:
            matches = re.finditer(pattern, chunk.text, re.IGNORECASE)
            for match in matches:
                # Extract snippet (200 chars after match to get full problem text)
                start = match.start()
                snippet = chunk.text[start:start + 250].strip()
                # Clean up snippet (collapse multiple spaces/newlines)
                snippet = re.sub(r'\s+', ' ', snippet)
                
                problem = PracticeProblem(
                    file_id=chunk.file_id,
                    filename=chunk.filename,
                    page=chunk.page_start,
                    snippet=snippet
                )
                problems.append(problem)
                
                if len(problems) >= max_problems:
                    return problems
    
    return problems[:max_problems]


def extract_key_terms(
    chunks: list[Chunk],
    top_k: int = 8,
    min_frequency: int = 2
) -> list[str]:
    """
    Extract key terms from top chunks.
    
    Looks for capitalized phrases (2-4 words) and ranks by frequency.
    
    Args:
        chunks: List of chunks to analyze
        top_k: Maximum number of terms to return
        min_frequency: Minimum appearances across chunks
        
    Returns:
        List of key term strings
    """
    # Common words to exclude
    stopwords = {
        'The', 'A', 'An', 'This', 'That', 'These', 'Those', 'In', 'On', 'At',
        'To', 'For', 'Of', 'With', 'By', 'From', 'As', 'Is', 'Are', 'Was',
        'Were', 'Be', 'Been', 'Being', 'Have', 'Has', 'Had', 'Do', 'Does',
        'Did', 'Will', 'Would', 'Could', 'Should', 'May', 'Might', 'Must',
        'Can', 'Chapter', 'Section', 'Figure', 'Table', 'Page'
    }
    
    # Pattern for capitalized phrases (2-4 words)
    pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b'
    
    term_counts = Counter()
    
    for chunk in chunks[:5]:  # Only look at top 5 chunks
        matches = re.findall(pattern, chunk.text)
        for match in matches:
            # Filter stopwords
            words = match.split()
            if not any(word in stopwords for word in words):
                term_counts[match] += 1
    
    # Filter by frequency and return top K
    terms = [
        term for term, count in term_counts.most_common(top_k * 2)
        if count >= min_frequency
    ]
    
    return terms[:top_k]


def enrich_topic(
    topic_bullet: str,
    chapter_number: int,
    chapter_title: str,
    index,
    mapping: dict,
    chunks_path: Path,
    top_k: int = 10,
    min_score: float = 0.6,
    use_chapter_filter: bool = True,
    fallback_threshold: int = 3
) -> EnrichedTopic:
    """
    Enrich a single topic bullet with textbook evidence.
    
    Args:
        topic_bullet: Learning objective text
        chapter_number: Chapter this topic belongs to
        chapter_title: Chapter title
        index: FAISS index
        mapping: Row to chunk mapping
        chunks_path: Path to chunks JSONL
        top_k: Number of chunks to retrieve
        min_score: Minimum similarity score
        use_chapter_filter: Whether to filter by chapter
        fallback_threshold: If chapter filter returns < this, try without filter
        
    Returns:
        EnrichedTopic with reading pages, problems, terms, and confidence
    """
    # Embed query
    query_embedding = embed_query(topic_bullet)
    
    # Build filters
    filters = {"min_score": min_score}
    if use_chapter_filter and chapter_number:
        filters["chapter_number"] = chapter_number
    
    # Search with chapter filter
    results = search_index(
        query_embedding=query_embedding,
        index=index,
        mapping=mapping,
        chunks_path=chunks_path,
        top_k=top_k,
        filters=filters
    )
    
    # Fallback: if too few results with chapter filter, try without
    if use_chapter_filter and len(results) < fallback_threshold:
        filters.pop("chapter_number", None)
        results = search_index(
            query_embedding=query_embedding,
            index=index,
            mapping=mapping,
            chunks_path=chunks_path,
            top_k=top_k,
            filters=filters
        )
    
    # If still no results, return empty enrichment
    if not results:
        return EnrichedTopic(
            chapter=chapter_number,
            chapter_title=chapter_title,
            bullet=topic_bullet,
            reading_pages=ReadingPages(file_id="", filename="", page_ranges=[]),
            confidence_score=0.0,
            chunks_retrieved=0,
            notes="No relevant chunks found above threshold"
        )
    
    # Load full chunks
    all_chunks = load_chunks_jsonl(chunks_path)
    chunk_dict = {c.chunk_id: c for c in all_chunks}
    
    retrieved_chunks = []
    for result in results:
        chunk = chunk_dict.get(result["chunk_id"])
        if chunk:
            retrieved_chunks.append(chunk)
    
    # Calculate confidence score (average of retrieval scores)
    avg_score = np.mean([r["score"] for r in results])
    
    # Extract reading pages from all retrieved chunks
    # Note: section_type categorization was removed as unreliable
    all_pages = []
    for chunk in retrieved_chunks:
        all_pages.extend(range(chunk.page_start, chunk.page_end + 1))
    
    page_ranges = consolidate_page_ranges(all_pages)
    
    # Get file info from first chunk
    first_chunk = retrieved_chunks[0] if retrieved_chunks else None
    reading_pages = ReadingPages(
        file_id=first_chunk.file_id if first_chunk else "",
        filename=first_chunk.filename if first_chunk else "",
        page_ranges=page_ranges
    )
    
    # Extract practice problems from all chunks
    # Section type filtering disabled - extract from any chunk
    practice_problems = extract_practice_problems(retrieved_chunks, max_problems=5)
    
    # Extract key terms
    key_terms = extract_key_terms(retrieved_chunks[:5], top_k=8)
    
    # Store top chunk excerpts for question generation (limit to 2-3, max 400 chars each)
    top_chunk_excerpts = []
    for chunk in retrieved_chunks[:3]:
        excerpt = chunk.text.strip()
        # Truncate long chunks
        if len(excerpt) > 400:
            excerpt = excerpt[:400] + "..."
        top_chunk_excerpts.append(excerpt)
    
    # Add notes for low confidence
    notes = ""
    if avg_score < 0.6:
        notes = "Low confidence: textbook may not align well with this objective"
    
    return EnrichedTopic(
        chapter=chapter_number,
        chapter_title=chapter_title,
        bullet=topic_bullet,
        reading_pages=reading_pages,
        practice_problems=practice_problems,
        key_terms=key_terms,
        confidence_score=float(avg_score),
        chunks_retrieved=len(results),
        notes=notes,
        top_chunks=top_chunk_excerpts
    )


def enrich_coverage(
    coverage: ExamCoverage,
    index_path: Path,
    mapping_path: Path,
    chunks_path: Path,
    top_k: int = 10,
    min_score: float = 0.6,
    use_chapter_filter: bool = True
) -> EnrichedCoverage:
    """
    Enrich exam coverage with textbook evidence via RAG.
    
    Args:
        coverage: Exam coverage to enrich
        index_path: Path to FAISS index
        mapping_path: Path to row→chunk mapping
        chunks_path: Path to chunks JSONL
        top_k: Number of chunks to retrieve per topic
        min_score: Minimum similarity score threshold
        use_chapter_filter: Whether to use chapter-aware filtering
        
    Returns:
        EnrichedCoverage with reading pages, problems, and terms
    """
    print(f"\n🔍 RAG Scout: Enriching {coverage.exam_name}")
    print(f"   Exam ID: {coverage.exam_id}")
    print(f"   Chapters: {coverage.chapters}")
    print(f"   Strategy: {'Chapter-aware' if use_chapter_filter else 'Full-textbook'} filtering")
    print()
    
    # Load FAISS index and mapping
    print("Loading index...", flush=True)
    index = load_faiss_index(index_path)
    mapping = load_chunk_mapping(mapping_path)
    print(f"✓ Loaded index with {index.ntotal} vectors\n")
    
    # Enrich each topic
    enriched_topics = []
    total_topics = sum(len(chapter_topic.bullets) for chapter_topic in coverage.topics)
    
    topic_count = 0
    for chapter_topic in coverage.topics:
        chapter_num = chapter_topic.chapter
        chapter_title = chapter_topic.chapter_title
        
        print(f"Chapter {chapter_num}: {chapter_title}")
        
        for bullet in chapter_topic.bullets:
            topic_count += 1
            # Truncate bullet for display
            bullet_preview = bullet[:70] + "..." if len(bullet) > 70 else bullet
            print(f"  [{topic_count}/{total_topics}] {bullet_preview}")
            
            enriched = enrich_topic(
                topic_bullet=bullet,
                chapter_number=chapter_num,
                chapter_title=chapter_title,
                index=index,
                mapping=mapping,
                chunks_path=chunks_path,
                top_k=top_k,
                min_score=min_score,
                use_chapter_filter=use_chapter_filter
            )
            
            enriched_topics.append(enriched)
            
            # Show quick stats
            pages_str = f"{len(enriched.reading_pages.page_ranges)} ranges" if enriched.reading_pages.page_ranges else "none"
            problems_str = f"{len(enriched.practice_problems)} problems" if enriched.practice_problems else "none"
            terms_str = f"{len(enriched.key_terms)} terms" if enriched.key_terms else "none"
            conf_emoji = "🟢" if enriched.confidence_score >= 0.75 else "🟡" if enriched.confidence_score >= 0.6 else "🔴"
            
            print(f"      → {conf_emoji} Pages: {pages_str}, Problems: {problems_str}, Terms: {terms_str} (conf: {enriched.confidence_score:.2f})")
        
        print()  # Blank line between chapters
    
    # Create enriched coverage
    enriched_coverage = EnrichedCoverage(
        exam_id=coverage.exam_id,
        exam_name=coverage.exam_name,
        exam_date=coverage.exam_date,
        source_file_id=coverage.source_file_id,
        topics=enriched_topics
    )
    
    # Calculate stats
    enriched_coverage.calculate_stats()
    
    # Print summary
    print("="*70)
    print("📊 Enrichment Summary")
    print("="*70)
    print(f"Total topics: {enriched_coverage.total_topics}")
    print(f"  🟢 High confidence (≥0.75): {enriched_coverage.high_confidence_count}")
    print(f"  🟡 Medium confidence (0.6-0.75): {enriched_coverage.medium_confidence_count}")
    print(f"  🔴 Low confidence (<0.6): {enriched_coverage.low_confidence_count}")
    
    if enriched_coverage.low_confidence_count > 0:
        pct = (enriched_coverage.low_confidence_count / enriched_coverage.total_topics) * 100
        print(f"\n⚠️  Warning: {pct:.1f}% of topics have low confidence matches.")
        print("   The textbook may not align perfectly with exam coverage.")
    
    return enriched_coverage
