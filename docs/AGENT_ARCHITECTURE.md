# Agent Architecture

## Overview

The Study Agent system is divided into **4 specialized agents** that handle distinct processes:

1. **Ingest Agent** - Data ingestion and preprocessing
2. **Planner Agent** - Study plan generation
3. **Tutor Agent** - Q&A and concept explanation
4. **Root Agent** - Orchestration and user interaction

Each agent is autonomous but can be composed/called by the root agent.

---

## Agent 1: Ingest Agent 📥

**Purpose:** Handle all data ingestion, preprocessing, and indexing

### Processes Owned:
1. **File Management**
   - Scan upload directory for new/modified files
   - Update manifest with file metadata
   - Track file status (pending, processing, processed, error)

2. **Text Extraction**
   - Extract text from PDFs (textbooks, syllabi, exam overviews)
   - Cache extracted text to avoid re-processing
   - Handle page-level extraction with metadata

3. **Document Classification**
   - Classify documents as: textbook, exam_overview, or syllabus
   - Rule-based (no LLM needed)
   - Store classification in manifest

4. **Textbook Processing**
   - Extract table of contents (chapter structure)
   - Chunk textbook into semantic units
   - Detect chapter boundaries and section headers
   - Store chunks with metadata (file_id, chapter, page_start, page_end)

5. **Embedding & Indexing**
   - Generate embeddings for all chunks using Gemini
   - Build FAISS index for fast similarity search
   - Maintain chunk-to-row mapping for retrieval

### Tools Used:
- `update_manifest()` - Scan directory and update file tracking
- `extract_text(file_id)` - Extract text from PDF
- `classify_docs()` - Classify document type
- `extract_toc(file_id)` - Get textbook chapter structure
- `chunk_textbook(file_id)` - Break textbook into chunks
- `build_index()` - Create embeddings and FAISS index

### Success Criteria:
- ✅ All uploaded files are processed and indexed
- ✅ Chunks are retrievable via semantic search
- ✅ Documents are correctly classified

### Example User Interactions:
- "I uploaded new files, can you process them?"
- "Index my textbook"
- "What files do you have?"

---

## Agent 2: Planner Agent 📅

**Purpose:** Generate personalized study schedules from exam coverage

### Processes Owned:
1. **Exam Coverage Extraction**
   - Parse exam overview PDFs
   - Extract: exam name, date, chapters covered, learning objectives
   - Structure objectives by chapter and topic

2. **RAG Enrichment** (Core process)
   - For each exam learning objective:
     - Query FAISS for relevant textbook chunks
     - Extract reading pages (consolidated ranges)
     - Find practice problems in chunks
     - Extract key terms
     - Store top chunk excerpts for question generation
   - Calculate confidence scores for each match
   - Store enriched coverage with textbook evidence

3. **Schedule Generation**
   - Input: Exam IDs, date range, minutes per day, strategy
   - Estimate time per topic (based on complexity, practice problems, chapter)
   - Apply scheduling strategy:
     - **Round-robin**: Alternate between exams evenly
     - **Priority-first**: Complete first exam, then second
     - **Balanced**: Equalize total minutes per exam
   - Allocate topics to days (skip weekends)
   - Generate study questions from RAG chunks (optional)

4. **Plan Export**
   - Export to Markdown (human-readable daily schedule)
   - Export to CSV (spreadsheet-compatible)
   - Export to JSON (programmatic access)

### Tools Used:
- `extract_coverage(file_id)` - Parse exam overview
- `enrich_coverage(exam_id)` - RAG enrichment with textbook
- `generate_plan(exam_ids, dates, minutes, strategy)` - Create schedule
- `export_plan(plan_id, format)` - Export to readable format
- `check_readiness(exam_ids)` - Verify prerequisites

### Success Criteria:
- ✅ Exam coverage accurately extracted
- ✅ Learning objectives matched to textbook pages (high confidence)
- ✅ Study schedule is balanced and realistic
- ✅ Plans include reading pages, practice problems, study questions

### Example User Interactions:
- "Create a study plan for my midterm"
- "I have 2 exams in 3 weeks, help me schedule"
- "Show me what's covered on exam 1"
- "Export my plan as markdown"

---

## Agent 3: Tutor Agent 🎓

**Purpose:** Answer study questions using RAG over textbook content

### Processes Owned:
1. **Question Understanding**
   - Parse user question
   - Identify key concepts and keywords
   - Determine if exam-scoped or general

2. **Context Retrieval**
   - Query FAISS for relevant textbook chunks
   - If exam specified, filter to exam's chapters
   - Rank chunks by relevance
   - Retrieve top 3-5 chunks with page numbers

3. **Answer Generation**
   - Use LLM with retrieved chunks as context
   - Generate answer grounded in textbook content
   - Include citations (page numbers)
   - Explain concepts step-by-step

4. **Follow-up Suggestions**
   - Suggest related concepts to study
   - Recommend practice problems from chunks
   - Link to relevant exam objectives

### Tools Used:
- `search_textbook(query, exam_scope, top_k)` - Semantic search
- `retrieve_chunks(chunk_ids)` - Get full chunk content
- `generate_answer(question, context)` - LLM-based answer with citations

### Success Criteria:
- ✅ Answers are accurate and grounded in textbook
- ✅ Citations include page numbers
- ✅ Explanations are clear and pedagogical
- ✅ No hallucination (all facts from retrieved chunks)

### Example User Interactions:
- "What is statistical significance?"
- "Explain the difference between population and sample"
- "How do I calculate a confidence interval?"
- "What's covered in Chapter 3 for my exam?"

---

## Agent 4: Root Agent 🎯

**Purpose:** Orchestrate the system and manage user interactions

### Responsibilities:
1. **Intent Recognition**
   - Parse user message
   - Determine which agent to route to
   - Extract parameters (exam names, dates, concepts)

2. **Automatic Sync** (on every turn)
   - Run `update_manifest()` to detect new files
   - Process any pending files through ingest pipeline
   - Keep index up-to-date

3. **Readiness Checking**
   - Before generating plans: verify coverage exists, enrichment complete, index built
   - If missing prerequisites, guide user to upload materials
   - Provide clear "missing materials" messages

4. **Agent Coordination**
   - Route to Ingest Agent for file processing
   - Route to Planner Agent for schedule generation
   - Route to Tutor Agent for Q&A
   - Synthesize responses from multiple agents if needed

5. **Error Handling**
   - Graceful failures with actionable messages
   - Suggest next steps when materials are missing
   - Warn on low-confidence matches

6. **Session Management**
   - Track user's current plan
   - Remember uploaded files
   - Maintain conversation context

### Tools Used:
- `sync_files()` - Auto-sync on every turn
- `check_readiness(intent, params)` - Verify prerequisites
- `list_available_exams()` - Show what's ready
- All tools from other agents (via delegation)

### Routing Logic:

```python
if intent == "upload" or "process files":
    → Ingest Agent
    
elif intent == "create plan" or "schedule exams":
    → Planner Agent
    
elif intent == "explain" or "what is" or question:
    → Tutor Agent
    
elif intent == "show exams" or "list files":
    → Direct tool call (list_available_exams)
    
else:
    → General conversation or clarification
```

### Success Criteria:
- ✅ Users always know what materials are available
- ✅ System auto-syncs without manual prompting
- ✅ Errors are clear and actionable
- ✅ Smooth handoffs between agents

### Example User Interactions:
- "Help me prepare for my exams" → Orchestrates full flow
- "What can you do?" → Explains capabilities
- "Create a study plan" → Checks readiness → Routes to Planner
- "Explain Chapter 3" → Routes to Tutor

---

## Agent Interaction Flow

```
User Message
     ↓
Root Agent (Intent recognition + Sync)
     ↓
   ┌─────────────┬──────────────┬─────────────┐
   ↓             ↓              ↓             ↓
Ingest Agent  Planner Agent  Tutor Agent   Direct Tools
   ↓             ↓              ↓             ↓
Results synthesized by Root Agent
     ↓
User Response
```

---

## Data Flow Between Agents

### 1. Upload → Plan Flow
```
User uploads files
  → Ingest Agent: extract, classify, chunk, index
  → Planner Agent: extract coverage, enrich with RAG, generate plan
  → User receives: Study schedule with pages and questions
```

### 2. Question Flow
```
User asks question
  → Tutor Agent: search FAISS, retrieve chunks, generate answer
  → User receives: Answer with page citations
```

### 3. End-to-End Example
```
User: "I have two exams coming up, help me study"

Root Agent:
  1. Syncs files (finds 2 exam overviews, 1 textbook)
  2. Routes to Ingest Agent → processes all files
  3. Routes to Planner Agent:
     - Extracts coverage for both exams
     - Enriches with textbook (RAG Scout)
     - Generates 20-day interleaved schedule
  4. Returns plan summary + offers export
  
User: "Explain the concept on page 45"

Root Agent:
  1. Routes to Tutor Agent
  2. Tutor retrieves chunks around page 45
  3. Generates explanation
  4. Returns answer with context
```

---

## Technical Implementation Notes

### Agent Framework: Google ADK
- Each agent is an `Agent` instance with tools
- Agents can call each other (composition)
- Tools are Python functions wrapped in ADK schema

### Tool Design Pattern
```python
@tool
def tool_name(param: str) -> dict:
    """Tool description for LLM."""
    # Implementation
    return {"status": "success", "data": {...}}
```

### State Management
- Session state stored in `.adk/session.db`
- File state in `storage/state/manifest.json`
- No external DB needed (file-based)

### Error Handling
- All tools return structured dicts with status
- Root agent interprets errors and provides user-friendly messages
- Never crash - always return actionable feedback

---

## Next Steps for Implementation

1. **Define all tool functions** in `app/agents/tools.py`
2. **Implement each agent** with proper tools and instructions
3. **Build Root Agent routing logic**
4. **Test each agent independently**
5. **Test full orchestration**
6. **Add logging and monitoring**

---

## Success Metrics

**Ingest Agent:**
- 100% of uploaded files successfully processed
- Avg processing time < 30s per file

**Planner Agent:**
- 90%+ high-confidence matches (RAG score ≥ 0.75)
- Plans completed within 2 minutes
- No hallucinated page numbers

**Tutor Agent:**
- 100% answers include page citations
- No hallucinations (all facts from chunks)
- Avg response time < 5s

**Root Agent:**
- 100% of intents correctly routed
- Auto-sync works on every turn
- Clear error messages for all failure modes

---

**This architecture ensures:**
- ✅ Separation of concerns
- ✅ Each agent has a clear, focused purpose
- ✅ Agents can be developed and tested independently
- ✅ Root agent provides seamless user experience
- ✅ System is extensible (easy to add new agents)
