# Storage Directory

Documentation for the `storage/` directory structure.

---

## Overview

The `storage/` directory holds all inputs and generated state:

- **User uploads** — PDFs in `storage/uploads/`
- **State** — Manifest, extracted text, coverage, chunks, index, and plans under `storage/state/`
- **Logs** — Optional logs in `storage/logs/`

All paths are **local** and **persistent**. The layout matches the project spec (deterministic data plane + agentic logic).

---

## Directory Structure

```
storage/
├── uploads/              # User places PDFs here (syllabus, exam overviews, textbooks)
├── state/               # All generated artifacts
│   ├── manifest.json    # File inventory, SHA-256, doc_type, status
│   ├── extracted_text/  # Per-file extracted text cache (by file_id)
│   ├── textbook_metadata/  # Per-textbook TOC / chapter boundaries (by file_id)
│   ├── chunks/          # chunks.jsonl (+ optional chunk_index.json)
│   ├── index/           # FAISS index + row_to_chunk_id mapping
│   ├── coverage/        # Per-exam coverage JSON (by exam file_id)
│   ├── enriched_coverage/  # Coverage + RAG-sourced pages/problems (by file_id)
│   └── plans/           # Generated study plans (UUID.json, UUID.md)
├── logs/                # Tool/agent logs (optional)
└── topics/              # Reserved (e.g. .gitkeep)
```

---

## `uploads/`

**Purpose**: Source PDFs (syllabus, exam overviews, textbooks).

**User responsibility**:
- Place PDFs in `storage/uploads/`
- Use clear filenames (e.g. `PHYS 234 - Syllabus.pdf`, `Midterm 1 Overview.pdf`)

**Notes**:
- Only PDFs with extractable text are supported (no OCR).
- The manifest tracks files by path and SHA-256; changed files are re-processed.

**Handling changes**:
- **Add**: New file → manifest marks it `new` → pipeline processes it.
- **Replace**: Same path, new content → SHA changes → status `stale` → re-processed.
- **Remove**: File no longer in `uploads/` (manifest can still reference it until next scan).

---

## `state/manifest.json`

**Purpose**: Single source of truth for uploaded files and processing status.

**Contents** (conceptually):
- `version`, `last_scan`
- `files[]`: `file_id`, `path`, `filename`, `sha256`, `size_bytes`, `modified_time`, `doc_type`, `status`, `derived[]`, optional `error`

**doc_type**: One of `syllabus`, `exam_overview`, `textbook`, `other`, `unknown` (set by classification).

**status**: `new` | `processed` | `stale` | `error`.

**Usage**: Ingest and root agent use it for sync, readiness, and routing.

---

## `state/extracted_text/`

**Purpose**: Cached extracted text per file (`<file_id>.json`).

**Contents**: `file_id`, `path`, `num_pages`, `pages[]`, `full_text`, `first_page`, `extracted_at`.

**Lifecycle**: Filled by text extraction; re-created when file is re-processed.

---

## `state/textbook_metadata/`

**Purpose**: Table-of-contents / chapter boundaries per textbook (`<file_id>.json`).

**Contents**: `file_id`, `filename`, `chapters[]` with `chapter`, `title`, `page_start`, `page_end`, etc.

**Usage**: Chapter-aware chunking and RAG filtering (e.g. retrieval by chapter).

---

## `state/chunks/`

**Purpose**: Textbook chunks in `chunks.jsonl` (one JSON object per line).

**Chunk fields** (typical): `chunk_id`, `file_id`, `page_start`, `page_end`, `text`, token metadata, optional `chapter_number` / `chapter_title`.

**Usage**: Embedding and FAISS index are built from these; Tutor and RAG Scout retrieve by chunk_id.

---

## `state/index/`

**Purpose**: FAISS vector index and row → chunk_id mapping.

**Typical files**:
- `faiss.index` — FAISS index (e.g. IndexFlatIP for cosine similarity).
- `row_to_chunk_id.json` — Mapping from index row to `chunk_id`.

**Usage**: Semantic search for RAG (Tutor, RAG Scout). Rebuilt when chunks change.

---

## `state/coverage/`

**Purpose**: Exam scope per exam overview file (`<file_id>.json`).

**Contents**: `exam_id`, `exam_name`, `exam_date`, `chapters[]`, `topics[]` (chapter + bullets), `source_file_id`, `generated_at`.

**Usage**: Source of truth for “what’s on the exam”; input to enrichment and planning.

---

## `state/enriched_coverage/`

**Purpose**: Coverage plus RAG-sourced evidence per exam (`<file_id>.json`).

**Contents**: Same as coverage plus, per topic: `reading_pages`, `practice_problems`, `key_terms`, `confidence_score`.

**Usage**: Planner uses this to generate study plans with concrete pages and problems.

---

## `state/plans/`

**Purpose**: Generated study plans.

**Formats**: One plan = `<plan_id>.json` (machine-readable) and `<plan_id>.md` (human-readable).

**Usage**: Exported via CLI or agent (e.g. `export_plan`); user can open the `.md` file.

---

## File Lifecycle (summary)

1. **Upload** → files in `storage/uploads/`.
2. **Sync** → manifest updated; new/stale files get extracted text, classification, and (for textbooks) TOC, chunking, and index.
3. **Exam overviews** → coverage extracted → optionally enriched → plans generated into `storage/state/plans/`.

---

## Backup and cleanup

**Backup** (example):

```bash
tar -czf study_agent_backup.tar.gz storage/
```

**Clean state but keep uploads** (artifacts regenerated by re-running pipeline):

```bash
rm -rf storage/state/extracted_text/*
rm -rf storage/state/textbook_metadata/*
rm -rf storage/state/chunks/*
rm -rf storage/state/index/*
rm -rf storage/state/coverage/*
rm -rf storage/state/enriched_coverage/*
# Optionally keep or remove plans:
# rm -rf storage/state/plans/*
```

**Full reset** (including uploads):

```bash
rm -rf storage/uploads/*
# then run the cleanup above if desired
```

Use the project’s `reset_data.sh` / `reset_data_keep_plans.sh` if they exist and match your intent.

---

## Security and privacy

- All data is **local**; no automatic cloud upload of PDFs or plans.
- Add `storage/` (or at least `storage/state/`, `storage/uploads/`) to `.gitignore` if the repo is shared and contains private materials.

---

**See also**: [Project spec](../project.md), [Execution plan](../docs/EXECUTION_PLAN.md), [Architecture](../docs/ARCHITECTURE.md).
