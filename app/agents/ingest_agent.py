"""Ingest agent: processes uploads, extracts text, chunks, and indexes."""
from google.adk.agents.llm_agent import Agent
from app.agents.tools import (
    list_files,
    sync_files,
    extract_text,
    classify_document,
    extract_coverage,
    extract_toc_tool,
    chunk_textbook,
    build_index
)

ingest_agent = Agent(
    model="gemini-3-flash-preview",
    name="ingest_agent",
    description="Processes documents: PDF extraction, classification, chunking, embedding, and indexing.",
    instruction="""You handle all data ingestion for the Study Agent system.

Core Workflow:
1. sync_files() or list_files() - Get file IDs and check status/doc_type
2. For each file: extract_text(file_id) if needed
3. For each file: classify_document(file_id) if doc_type='unknown'
4. For exam overviews: extract_coverage(file_id)
5. For textbooks: extract_toc_tool(file_id) → chunk_textbook(file_id)
   (Note: chunking uses coverage files to focus on required chapters)
6. build_index() - After all textbooks are chunked

Status & Caching:
- Tools automatically skip if status='processed' (cached)
- Only process files with status='new' or 'stale'
- Tools validate prerequisites and return clear errors if missing

Key Rules:
- Always classify files with doc_type='unknown' before other processing
- Extract file_id from sync_files() or list_files() return data
- Only textbooks need TOC extraction and chunking
- Build index only once, after all textbooks are ready
- Report progress clearly at each step""",
    tools=[
        list_files,
        sync_files,
        extract_text,
        classify_document,
        extract_coverage,
        extract_toc_tool,
        chunk_textbook,
        build_index
    ]
)
