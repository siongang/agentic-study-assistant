# Agent Process Mapping

## Core Processes in Study Agent

### Process 1: Data Ingestion Pipeline 📥
**Owner: Ingest Agent**

```
Upload Directory
    ↓
[1] Scan & Track (manifest)
    ↓
[2] Extract Text (PDF → JSON)
    ↓
[3] Classify (textbook/exam_overview/syllabus)
    ↓
    ├─→ [4a] Textbook Path:
    │       - Extract TOC
    │       - Chunk by chapters
    │       - Generate embeddings
    │       - Build FAISS index
    │
    └─→ [4b] Exam Path:
            - Store for coverage extraction
            - Ready for Planner Agent
```

**Input:** Raw PDF files in `uploads/`  
**Output:** Indexed, searchable chunks in FAISS  
**Duration:** 20-60s per file  
**Status Check:** `check_readiness()`

---

### Process 2: Coverage Extraction & Enrichment 📋
**Owner: Planner Agent**

```
Exam Overview PDF
    ↓
[1] Parse Structure
    - Exam name, date
    - Chapters covered
    - Learning objectives (bullets)
    ↓
[2] RAG Enrichment (for each objective)
    - Query: objective text → FAISS
    - Retrieve: top 10 chunks (filtered by chapter)
    - Extract:
        * Reading pages (consolidated ranges)
        * Practice problems (regex matching)
        * Key terms (capitalized phrases)
        * Top 3 chunk excerpts (for questions)
    - Calculate: confidence score (avg similarity)
    ↓
[3] Store Enriched Coverage
    - Save to storage/state/enriched_coverage/
    - Ready for plan generation
```

**Input:** Exam overview PDF + FAISS index  
**Output:** Enriched coverage with textbook evidence  
**Duration:** 1-3 min per exam (depends on topics)  
**Quality Metric:** Confidence score (target: ≥0.75)

---

### Process 3: Study Plan Generation 📅
**Owner: Planner Agent**

```
Enriched Coverage(s) + Date Range + Preferences
    ↓
[1] Work Queue Assembly
    - Collect all topics from all exams
    - Estimate time per topic (30-75 min)
        * +20 if practice problems > 2
        * +15 if foundational chapters (1-3)
        * +10 if low confidence (<0.7)
    ↓
[2] Apply Scheduling Strategy
    ├─→ Round-robin: Alternate exams evenly
    ├─→ Priority-first: Complete exam 1, then exam 2
    └─→ Balanced: Equalize total minutes per exam
    ↓
[3] Allocate to Days
    - Fill each day up to max minutes (e.g., 90)
    - Skip weekends (optional)
    - Create StudyDay → StudyBlock structure
    ↓
[4] Generate Study Questions (optional)
    - For each block: LLM call with chunk excerpts
    - Generate 1 contextual question per topic
    ↓
[5] Export Plan
    - JSON (full structure)
    - Markdown (daily schedule)
    - CSV (spreadsheet)
```

**Input:** 1-N enriched coverages + preferences  
**Output:** Complete study schedule  
**Duration:** 1-5 min (depends on question generation)  
**Formats:** JSON, Markdown, CSV

---

### Process 4: Q&A / Tutoring 🎓
**Owner: Tutor Agent**

```
User Question
    ↓
[1] Query Understanding
    - Extract key concepts
    - Identify exam scope (if mentioned)
    - Determine question type (definition/explanation/calculation)
    ↓
[2] Context Retrieval
    - Embed query → FAISS search
    - Filter by chapter if exam scoped
    - Retrieve top 3-5 chunks
    - Extract page numbers
    ↓
[3] Answer Generation
    - LLM prompt:
        * System: "Answer based ONLY on context"
        * Context: Retrieved chunks
        * Question: User query
    - Generate explanation
    - Add page citations
    ↓
[4] Enhance Response
    - Suggest related concepts
    - Link to practice problems
    - Connect to exam objectives
```

**Input:** Natural language question  
**Output:** Answer + page citations  
**Duration:** 2-5s  
**Quality:** No hallucination (grounded in chunks)

---

### Process 5: Orchestration & Readiness 🎯
**Owner: Root Agent**

```
User Message
    ↓
[1] Auto-Sync (every turn)
    - Update manifest
    - Process new/modified files
    - Keep index current
    ↓
[2] Intent Recognition
    - Parse user request
    - Extract parameters (exam IDs, dates, concepts)
    ↓
[3] Readiness Check
    - Do we have required materials?
    - Are prerequisites met?
    ↓
    ├─→ Ready: Route to appropriate agent
    │
    └─→ Not Ready: Guide user
            - "Upload exam overview for PHYS 234"
            - "Please upload textbook: Triola Statistics"
            - "Files are being processed (30s remaining)"
    ↓
[4] Agent Coordination
    - Delegate to specialist agent
    - Collect results
    - Synthesize response
    ↓
[5] User Response
    - Format results
    - Suggest next actions
    - Track session state
```

**Input:** Any user message  
**Output:** Appropriate response or agent delegation  
**Always:** Auto-sync + readiness check  

---

## Process Dependencies

```
Data Ingestion (Ingest Agent)
    ↓ (provides indexed textbook)
    ↓
Coverage Enrichment (Planner Agent)
    ↓ (provides enriched coverage)
    ↓
Plan Generation (Planner Agent)
    ↓ (provides schedule)
    ↓
Export (Planner Agent)

--- PARALLEL PATH ---

Data Ingestion (Ingest Agent)
    ↓ (provides indexed textbook)
    ↓
Q&A / Tutoring (Tutor Agent)
```

**Key Insight:** 
- Tutoring only needs: Ingest → Index
- Planning needs: Ingest → Enrichment → Plan
- Both paths start with Ingest Agent

---

## Agent → Process Mapping Summary

| Agent | Processes | Input | Output | Duration |
|-------|-----------|-------|--------|----------|
| **Ingest** | File scanning, text extraction, classification, chunking, embedding, indexing | PDFs | FAISS index | 20-60s/file |
| **Planner** | Coverage extraction, RAG enrichment, schedule generation, export | Exam PDFs + Index | Study plan | 2-5 min |
| **Tutor** | Question parsing, context retrieval, answer generation | Questions | Answers + citations | 2-5s |
| **Root** | Intent recognition, sync, readiness, routing, coordination | User messages | Agent responses | <1s |

---

## Critical Success Factors

**For Ingest Agent:**
- ✅ All files processed without errors
- ✅ Index buildable and searchable
- ✅ Classification accuracy 100%

**For Planner Agent:**
- ✅ High confidence matches (≥75%)
- ✅ Realistic time estimates
- ✅ Balanced schedules across exams

**For Tutor Agent:**
- ✅ Zero hallucinations
- ✅ All answers cite pages
- ✅ Fast response times

**For Root Agent:**
- ✅ Correct intent routing (100%)
- ✅ Clear error messages
- ✅ Seamless user experience

---

## Next: Tool Implementation

Now that we have clear process boundaries, we need to:

1. **Map existing CLI commands to ADK tools**
2. **Create tool wrappers** that agents can call
3. **Define agent instructions** based on their processes
4. **Implement routing logic** in Root Agent
5. **Add error handling** for each process
6. **Test each agent independently**

See: `docs/TOOL_MAPPING.md` (next doc to create)
