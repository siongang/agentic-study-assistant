# Data Flow Verification

## Phase 1: File Sync & Extraction

### 1.1 sync_files() 
**CLI**: `app/cli/update_manifest.py`
```python
update_manifest(uploads_dir, manifest_path)
```

**Tool**: `app/agents/tools.py:sync_files()`
```python
stats = update_manifest(UPLOADS_DIR, manifest_path)
# Returns: new_files[], updated_files[], all_files[]
```
✅ **Status**: CORRECT

---

### 1.2 extract_text(file_id)
**CLI**: `app/cli/extract_text.py`
```python
extracted, error = extract_text_from_pdf(
    file_path=file_path,
    file_id=file_entry.file_id,
    relative_path=file_entry.path
)
```

**Tool**: `app/agents/tools.py:extract_text()`
```python
extracted_text, error = extract_text_from_pdf(pdf_path, file_id, file_entry.path)
```
✅ **Status**: FIXED - Was missing parameters, now correct

---

### 1.3 classify_document(file_id)
**CLI**: `app/cli/classify_docs.py`
```python
result = classify_document(
    first_page=extracted.first_page,
    filename=file_entry.filename,
    full_text_sample=extracted.full_text[:2000]
)
```

**Tool**: `app/agents/tools.py:classify_document()`  
```python
result = classify_doc_llm(
    first_page=extracted_text_data.get("first_page", ""),
    filename=file_entry.filename,
    full_text_sample=extracted_text_data.get("full_text", "")[:2000]
)
```
✅ **Status**: FIXED - Was using wrong function, now correct

---

## Phase 2: TOC Extraction

### 2.1 extract_toc_tool(file_id)
**CLI**: `app/cli/extract_toc.py`
```python
toc_metadata, error = extract_toc(
    file_id=file_entry.file_id,
    pages=extracted.pages,
    filename=file_entry.filename
)
```

**Tool**: `app/agents/tools.py:extract_toc_tool()`
```python
toc_metadata, error = extract_toc(
    file_id=file_id,
    pages=extracted_text_data.get("pages", []),
    filename=file_entry.filename,
    max_toc_pages=30
)
```
✅ **Status**: FIXED - Was passing wrong params, now correct

---

## Phase 3: Chunking

### 3.1 chunk_textbook(file_id)
**CLI**: `app/cli/chunk_textbooks.py`
```python
chunks = chunk_textbook_smart(
    file_id=file_entry.file_id,
    extracted_text_dir=extracted_text_dir,
    textbook_metadata_dir=textbook_metadata_dir,
    coverage_dir=coverage_dir,
    filename=file_entry.filename,
    max_tokens=700,  # Note: CLI uses max_tokens
    overlap_tokens=100
)
```

**Tool**: `app/agents/tools.py:chunk_textbook()`
```python
chunks = chunk_textbook_smart(
    file_id=file_id,
    extracted_text_dir=extracted_text_dir,
    textbook_metadata_dir=textbook_metadata_dir,
    coverage_dir=coverage_dir,
    filename=file_entry.filename,
    target_tokens=700,  # Function actually takes both
    max_tokens=900,
    overlap_tokens=100
)
```
✅ **Status**: CORRECT - Function signature supports both params

**Saving**:
- CLI: `append_chunks_jsonl(chunks, chunks_output)`
- Tool: `save_chunks_jsonl(chunks, chunks_path, mode='a')`
✅ **Status**: CORRECT

---

## Phase 4: Index Building

### 4.1 build_index()
**CLI**: `app/cli/build_index.py`
```python
# Step 1: Get embeddings
embeddings, stats = get_or_compute_embeddings(
    chunks=chunks,
    cache_dir=cache_dir,
    embed_function=embed_fn
)

# Step 2: Build index
index = build_faiss_index(
    embeddings=embeddings,
    index_path=index_path,
    normalize=True
)

# Step 3: Build mapping
mapping = build_chunk_mapping(
    chunks=chunks,
    mapping_path=mapping_path
)
```

**Tool**: `app/agents/tools.py:build_index()`
```python
# Load chunks
chunks = load_chunks_jsonl(chunks_path)

# Generate embeddings  
chunk_texts = [chunk.text for chunk in chunks]
embeddings = embed_texts(chunk_texts, task_type="RETRIEVAL_DOCUMENT")

# Build index
build_faiss_index(embeddings, index_path, normalize=True)

# Build mapping
build_chunk_mapping(chunks, mapping_path)
```
⚠️ **Status**: MISSING EMBEDDING CACHE - Tool doesn't use cached embeddings!

---

## Phase 5: Coverage Extraction

### 5.1 extract_coverage(file_id)
**CLI**: `app/cli/extract_coverage.py`
```python
coverage, error = extract_exam_coverage(
    file_id=file_entry.file_id,
    max_chars=8000
)
```

**Tool**: `app/agents/tools.py:extract_coverage()`
```python
coverage, error = extract_coverage(
    file_id=file_id,
    max_chars=8000
)
```
❓ **Status**: NEED TO VERIFY FUNCTION IMPORT

---

## Phase 6: Coverage Enrichment

### 6.1 enrich_coverage_tool(exam_file_id)
**CLI**: `app/cli/enrich_coverage.py`
```python
enriched = enrich_coverage(
    coverage=coverage,
    index_path=index_path,
    mapping_path=mapping_path,
    chunks_path=chunks_path,
    top_k=10,
    min_score=0.6,
    use_chapter_filter=True
)
```

**Tool**: `app/agents/tools.py:enrich_coverage_tool()`
```python
enriched = enrich_coverage(
    coverage=coverage,
    index_path=index_path,
    mapping_path=mapping_path,
    chunks_path=chunks_path,
    top_k=10,
    min_score=0.6,
    use_chapter_filter=True
)
```
✅ **Status**: CORRECT

---

## Phase 7: Plan Generation

### 7.1 generate_plan()
**CLI**: `app/cli/generate_plan.py`
```python
plan = generate_multi_exam_plan(
    enriched_coverage_paths=enriched_paths,
    start_date=start,
    end_date=end,
    minutes_per_day=minutes_per_day,
    strategy=strategy,
    generate_questions=generate_questions
)
```

**Tool**: `app/agents/tools.py:generate_plan()`
```python
plan = generate_multi_exam_plan(
    enriched_coverage_paths=enriched_paths,
    start_date=start,
    end_date=end,
    minutes_per_day=minutes_per_day,
    strategy=strategy,
    generate_questions=generate_questions
)
```
✅ **Status**: CORRECT

---

## Issues Found

### 🔴 CRITICAL: build_index() - No Embedding Cache
The tool directly calls `embed_texts()` which is expensive and slow. It should use `get_or_compute_embeddings()` like the CLI does.

### 🟡 VERIFY: extract_coverage() function import
Need to verify the correct function is imported.

### 🟢 All other tools: CORRECT
