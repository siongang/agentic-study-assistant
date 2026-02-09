# System Architecture

> Deep technical documentation for the agentic study planner

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [System Layers](#system-layers)
3. [Agent Architecture](#agent-architecture)
4. [Data Flow](#data-flow)
5. [State Management](#state-management)
6. [Tool Design](#tool-design)
7. [Coverage Guarantee](#coverage-guarantee)
8. [Invalidation Strategy](#invalidation-strategy)

---

## Design Philosophy

### Core Principle

**Separate structure extraction from retrieval.**

The system follows this hierarchy:

```
PDFs
  ↓ deterministic extraction
Topics (source of truth)
  ↓ deterministic chunking
Chunks
  ↓ embedding
Vectors (for retrieval only)
```

**Key insight:** RAG is used for tutoring, not for planning or structure inference.

---

### Three-Layer Model

#### Layer 1: Artifacts (data)

All intermediate representations are persisted:

```
storage/
├── uploads/              # Source PDFs (user-provided)
└── state/
    ├── manifest.json    # File inventory, status, doc_type
    ├── extracted_text/  # Per-file text cache
    ├── textbook_metadata/  # TOC / chapter boundaries
    ├── chunks/          # chunks.jsonl
    ├── index/           # FAISS index + row mapping
    ├── coverage/        # Per-exam coverage
    ├── enriched_coverage/  # Coverage + RAG evidence
    └── plans/           # Generated study plans
```

This enables:
- **Reproducibility** — rerun any step without redoing previous steps
- **Debugging** — inspect intermediate states
- **Invalidation** — detect when artifacts are stale

#### Layer 2: Tools (deterministic logic)

Tools are **pure functions** with no LLM calls:

```python
# Example: topic_extractor
def extract_topics(pdf_pages: list[Page]) -> TopicInventory:
    """
    Deterministically extract topic structure.
    - Parse table of contents
    - Detect chapter/section headers
    - Build hierarchical topic tree
    """
    pass
```

Benefits:
- **Testable** — deterministic inputs → deterministic outputs
- **Fast** — no LLM latency
- **Reliable** — no hallucination risk

#### Layer 3: Agents (reasoning + orchestration)

Agents **decide when and how to use tools**:

```python
class RootAgent:
    def handle_message(self, msg: str):
        # Detect intent
        if self.is_new_textbook():
            return self.route_to_ingestion_agent()
        elif self.needs_replanning():
            return self.route_to_planner_agent()
        else:
            return self.route_to_tutor_agent()
```

Agents use LLMs for:
- Intent detection
- Natural language understanding
- Explanation generation

---

## System Layers

### Visual Overview

```
┌─────────────────────────────────────────────────────┐
│                   User (Terminal)                   │
└───────────────────────┬─────────────────────────────┘
                        │ natural language
                        ↓
┌─────────────────────────────────────────────────────┐
│                    RootAgent                        │
│  • Intent detection (LLM)                           │
│  • Material registry (state)                        │
│  • Agent routing (logic)                            │
└─┬─────────┬─────────┬─────────┬───────────────────┘
  │         │         │         │
  ↓         ↓         ↓         ↓
┌───────┐ ┌──────┐ ┌────────┐ ┌──────┐
│Ingest │ │Plan  │ │Verify  │ │Tutor │  ← Specialized agents
└───┬───┘ └───┬──┘ └───┬────┘ └───┬──┘
    │         │        │          │
    ↓         ↓        ↓          ↓
┌─────────────────────────────────────────────────────┐
│                      Tools                          │
│  parse_pdf  │  chunk_text  │  embed  │  schedule   │  ← Deterministic
└─────────────────────────────────────────────────────┘
    │         │        │          │
    ↓         ↓        ↓          ↓
┌─────────────────────────────────────────────────────┐
│                   Artifacts                         │
│  topics/  │  chunks/  │  indexes/  │  plans/       │  ← Persisted data
└─────────────────────────────────────────────────────┘
```

---

## Agent Architecture

### RootAgent (orchestrator)

**Responsibilities:**

1. **Intent detection**
   - Parse user message
   - Classify: ingestion, planning, tutoring, status check

2. **Material registry**
   - Track all textbooks (path, hash, status)
   - Detect changes (add, replace, remove)

3. **Routing**
   - Delegate to appropriate agent
   - Pass context (user query, materials, constraints)

**State:**

```python
@dataclass
class MaterialRegistry:
    materials: dict[str, Material]
    
@dataclass
class Material:
    course: str          # "Physics", "Biology"
    file_path: Path      # storage/uploads/physics.pdf
    file_hash: str       # SHA256
    ingested: bool       # Has been processed
    derived: list[str]   # state/extracted_text/..., state/textbook_metadata/..., etc.
    last_updated: datetime
```

**Invalidation logic:**

```python
def check_materials(self) -> list[Action]:
    actions = []
    
    # Scan storage/uploads/
    current_files = list(Path("storage/uploads").glob("*.pdf"))
    
    for file in current_files:
        hash = sha256(file.read_bytes())
        
        if file.name not in self.registry:
            # New textbook
            actions.append(Action.INGEST, file)
        elif self.registry[file.name].hash != hash:
            # Replaced textbook
            actions.append(Action.REINGEST, file)
            actions.append(Action.INVALIDATE_PLAN)
    
    # Check for removed files
    for name, material in self.registry.items():
        if material.file_path not in current_files:
            actions.append(Action.REMOVE, name)
            actions.append(Action.INVALIDATE_PLAN)
    
    return actions
```

---

### IngestionAgent

**Responsibilities:**

1. Parse PDF → raw pages
2. Extract topic inventory
3. Chunk text
4. Generate embeddings
5. Build vector index

**Workflow:**

```
PDF
 ↓ parse_pdf()
Pages: [{page: 1, text: "..."}, ...]
 ↓ extract_topics()
Topics: {course: "Physics", topics: [{id: "phys_1", title: "Kinematics", ...}]}
 ↓ chunk_text()
Chunks: [{chunk_id: "c_001", topic_id: "phys_1", text: "...", pages: [2,3]}]
 ↓ embed_chunks()
Vectors: [...] → ChromaDB
```

**Output artifacts:**

- `storage/state/extracted_text/<file_id>.json` — extracted text
- `storage/state/textbook_metadata/<file_id>.json` — TOC (textbooks)
- `storage/state/chunks/chunks.jsonl` — chunks with metadata
- `storage/state/index/` — FAISS index and row mapping

**Why this order?**

Topics must be extracted **before** chunking because:
- Chunks need `topic_id` tags
- Planning needs the complete topic list
- Coverage verification requires topic inventory

---

### PlannerAgent

**Responsibilities:**

1. Load topic inventories from all textbooks
2. Apply user constraints (exam dates, hours/day)
3. Allocate topics to dates
4. Generate human-readable plan

**Algorithm (deterministic):**

```python
def generate_plan(
    topics: list[Topic],
    exams: dict[str, date],
    hours_per_day: float
) -> StudyPlan:
    
    # 1. Build date range
    start = datetime.now().date()
    end = max(exams.values())
    days = date_range(start, end)
    
    # 2. Group topics by exam
    topic_groups = group_topics_by_exam(topics, exams)
    
    # 3. Estimate effort per topic
    for topic in topics:
        topic.effort_hours = estimate_effort(topic)
    
    # 4. Allocate topics to days
    plan = {}
    for day in days:
        # Get topics due by this day
        eligible = [t for t in topics if exams[t.course] >= day]
        
        # Schedule highest-priority topics
        capacity = hours_per_day
        plan[day] = []
        
        for topic in sorted(eligible, key=priority):
            if capacity >= topic.effort_hours:
                plan[day].append(topic)
                capacity -= topic.effort_hours
                topics.remove(topic)
    
    return StudyPlan(schedule=plan)
```

**Output:**

```markdown
# Study Plan (Feb 5 - Feb 25)

## Tuesday, Feb 5
- **Physics**: Kinematics (2.5 hrs, pp. 1-34)
- **Biology**: Cell Structure (1.5 hrs, pp. 12-45)

## Wednesday, Feb 6
- **Physics**: Dynamics (2.0 hrs, pp. 35-67)
...

## Coverage
- Physics: 18/18 topics ✓
- Biology: 24/24 topics ✓
```

---

### VerifierAgent

**Responsibilities:**

1. Check 100% topic coverage
2. Verify no topics scheduled after their exam
3. Ensure daily workload within limits

**Checks:**

```python
def verify_plan(plan: StudyPlan, topics: list[Topic]) -> VerificationResult:
    errors = []
    
    # Coverage check
    scheduled_topics = set(plan.all_topic_ids())
    all_topics = set(t.id for t in topics)
    
    uncovered = all_topics - scheduled_topics
    if uncovered:
        errors.append(f"Uncovered topics: {uncovered}")
    
    # Deadline check
    for day, topics in plan.schedule.items():
        for topic in topics:
            exam_date = get_exam_date(topic.course)
            if day > exam_date:
                errors.append(f"Topic {topic.id} scheduled after exam")
    
    # Workload check
    for day, topics in plan.schedule.items():
        total_hours = sum(t.effort_hours for t in topics)
        if total_hours > MAX_HOURS_PER_DAY:
            errors.append(f"Day {day} overloaded: {total_hours} hrs")
    
    return VerificationResult(valid=len(errors) == 0, errors=errors)
```

**Feedback loop:**

```
PlannerAgent generates plan
         ↓
VerifierAgent checks plan
         ↓
   [valid?]
    /     \
  yes      no
   ↓       ↓
 done   return errors → PlannerAgent adjusts → retry
```

---

### TutorAgent

**Responsibilities:**

1. Answer user questions about course material
2. Generate explanations grounded in textbooks
3. Cite page numbers and sections
4. Offer practice problems

**RAG workflow:**

```
User: "Explain acceleration"
         ↓
Embed query → [0.23, -0.45, ...]
         ↓
Retrieve top-k chunks from vector store
         ↓
Chunks: [
  {text: "Acceleration is...", topic: "phys_1_2", pages: [12, 13]},
  {text: "Newton's second law...", topic: "phys_3_1", pages: [67, 68]}
]
         ↓
LLM generates answer with citations
         ↓
Response: "Acceleration is the rate of change of velocity (Physics, pp. 12-13).
          It's related to force by Newton's second law: F=ma (pp. 67-68).
          
          Practice: If a 5kg object experiences 10N force, what's its acceleration?"
```

**Grounding strategy:**

- **Always cite sources** — page numbers mandatory
- **No hallucination** — if not in textbook, say so
- **Chunk metadata** — preserve topic_id, pages, section titles

---

## Data Flow

### Full System Flow

```
1. User places PDFs in storage/uploads/

2. User: "I added physics and biology textbooks. Plan for Feb 21 and Feb 25."

3. RootAgent:
   - Scans storage/uploads/ (via manifest)
   - Detects new/stale files
   - Routes to Ingest Agent

4. Ingest Agent:
   - Extracts text, classifies, chunks textbooks, builds index
   - Saves artifacts to storage/state/ (extracted_text, textbook_metadata, chunks, index)

5. RootAgent:
   - Detects intent: "make a plan"
   - Routes to Planner Agent

6. Planner Agent:
   - Loads coverage and enriched_coverage from storage/state/
   - Generates schedule
   - Saves to storage/state/plans/

7. VerifierAgent:
   - Checks coverage (100%?)
   - Checks constraints (deadlines, workload)
   - Returns validation result

8. RootAgent:
   - Returns plan to user

9. User: "Explain kinematics"

10. Tutor Agent:
    - Embeds query
    - Retrieves chunks from storage/state/index/ (FAISS)
    - Generates explanation
    - Cites pages
```

---

## State Management

### Material Registry (persistent)

Manifest stored in `storage/state/manifest.json` (file inventory). Material registry may be derived from it:

```json
{
  "files": [
    {
      "file_id": "...",
      "path": "uploads/physics.pdf",
      "sha256": "a3f2b9...",
      "doc_type": "textbook",
      "status": "processed",
      "derived": ["state/extracted_text/...", "state/textbook_metadata/..."]
    }
  ]
}
```

### Session State (ephemeral)

Held in memory during chat session:

```python
@dataclass
class SessionState:
    user_constraints: UserConstraints  # exam dates, hours/day
    current_plan: StudyPlan | None
    plan_valid: bool
    conversation_history: list[Message]
```

---

## Tool Design

### Principles

1. **Pure functions** — no side effects (except file I/O)
2. **No LLM calls** — deterministic only
3. **Testable** — clear inputs/outputs
4. **Fast** — optimized for local execution

### Example: Topic Extractor

```python
# tools/ingest/topic_extractor.py

from dataclasses import dataclass
from typing import List

@dataclass
class Topic:
    topic_id: str
    title: str
    page_range: tuple[int, int]
    subtopics: List['Topic']

def extract_topics(pdf_pages: list[dict]) -> TopicInventory:
    """
    Extract hierarchical topic structure from PDF.
    
    Strategy:
    1. Find table of contents (common patterns)
    2. Detect chapter headers (font size, bold)
    3. Build topic tree
    4. Assign IDs (e.g., phys_1, phys_1_1)
    """
    
    # Find TOC
    toc_pages = detect_toc(pdf_pages)
    
    if toc_pages:
        topics = parse_toc(toc_pages)
    else:
        # Fallback: detect headers in text
        topics = detect_headers(pdf_pages)
    
    # Assign IDs
    assign_topic_ids(topics, prefix="phys")
    
    return TopicInventory(course="Physics", topics=topics)
```

---

## Coverage Guarantee

### Problem

**How do we guarantee all topics are covered?**

### Solution

**Track topics from extraction → planning.**

#### Step 1: Extract complete topic inventory

```json
{
  "course": "Physics",
  "topics": [
    {"topic_id": "phys_1", "title": "Kinematics"},
    {"topic_id": "phys_2", "title": "Dynamics"},
    ...
  ]
}
```

This is the **source of truth**.

#### Step 2: Planning uses this inventory

```python
def generate_plan(topics: list[Topic]) -> StudyPlan:
    plan = {}
    
    for day in date_range:
        # Allocate topics to days
        ...
    
    # CRITICAL: Check for uncovered topics
    scheduled = set(plan.all_topic_ids())
    required = set(t.id for t in topics)
    
    uncovered = required - scheduled
    
    if uncovered:
        raise PlanningError(f"Uncovered topics: {uncovered}")
    
    return plan
```

#### Step 3: Verification double-checks

```python
def verify_coverage(plan: StudyPlan, topics: list[Topic]) -> bool:
    scheduled = set(plan.all_topic_ids())
    required = set(t.id for t in topics)
    
    return scheduled >= required  # All topics scheduled?
```

**Result:** Mathematically guaranteed coverage.

---

## Invalidation Strategy

### Trigger: Textbook changes

When a PDF is added/replaced/removed, the system must:

1. **Detect the change**
   ```python
   old_hash = registry["physics"].file_hash
   new_hash = sha256(Path("storage/uploads/physics.pdf").read_bytes())
   
   if old_hash != new_hash:
       # Textbook replaced
   ```

2. **Invalidate downstream artifacts**
   ```python
   def invalidate_material(file_id: str):
       # Remove old artifacts for this file
       # (extracted_text, textbook_metadata, and chunks/index updated by pipeline)
       Path(f"storage/state/extracted_text/{file_id}.json").unlink(missing_ok=True)
       # Chunks/index are global; pipeline re-chunks and rebuilds when needed
       
       # Mark plan as stale
       state.plan_valid = False
   ```

3. **Re-ingest**
   ```python
   ingestion_agent.ingest(course)
   ```

4. **Notify user**
   ```
   > Physics textbook was replaced.
   > Old study plan is now invalid.
   > Would you like me to regenerate the plan?
   ```

---

## Error Handling

### Categories

1. **User errors** — missing constraints, invalid dates
   - Handled by agents with clarifying questions

2. **Tool errors** — PDF parsing failure, embedding timeout
   - Logged, retried, then escalated to user

3. **Verification errors** — uncovered topics, overloaded days
   - Feedback loop: planner adjusts and retries

### Example: Verification feedback loop

```
PlannerAgent: "I allocated 42 topics across 18 days."
VerifierAgent: "ERROR: Topics phys_17, phys_18 are uncovered."
PlannerAgent: "Adjusting... added topics to Feb 10 and Feb 14."
VerifierAgent: "✓ All topics covered."
```

---

## Extensibility Points

### Adding a new agent

```python
# agents/quiz_agent.py

class QuizAgent:
    """Generate practice quizzes from course material."""
    
    def generate_quiz(self, topic_id: str, difficulty: str) -> Quiz:
        # Retrieve chunks for topic
        chunks = self.retriever.get_by_topic(topic_id)
        
        # Generate questions
        questions = self.llm.generate_questions(chunks, difficulty)
        
        return Quiz(topic=topic_id, questions=questions)
```

Register in `root_agent.py`:

```python
if "quiz" in user_message.lower():
    return self.quiz_agent.handle(message)
```

### Adding a new tool

```python
# tools/planning/optimizer.py

def optimize_schedule(plan: StudyPlan, constraints: Constraints) -> StudyPlan:
    """
    Improve plan by:
    - Spacing out difficult topics
    - Balancing daily workload
    - Maximizing retention
    """
    pass
```

Use in `PlannerAgent`:

```python
plan = allocator.generate_plan(topics, exams)
plan = optimizer.optimize_schedule(plan, constraints)
```

---

## Performance Considerations

### Ingestion

- **PDF parsing**: ~10 sec per 100 pages (PyMuPDF)
- **Topic extraction**: ~2 sec per textbook (no LLM)
- **Chunking**: ~5 sec per textbook
- **Embedding**: ~30 sec per 100 chunks (local model)

**Total ingestion time:** ~1-2 min per textbook

### Planning

- **Scheduling**: <1 sec (deterministic algorithm)
- **Verification**: <1 sec

### Tutoring

- **Retrieval**: ~100ms (ChromaDB)
- **LLM generation**: ~3 sec (Gemini)

---

## Testing Strategy

### Unit tests (tools)

```python
def test_topic_extractor():
    pages = load_fixture("physics_sample.json")
    topics = extract_topics(pages)
    
    assert len(topics) == 3
    assert topics[0].title == "Kinematics"
    assert topics[0].page_range == (1, 34)
```

### Integration tests (agents)

```python
def test_planning_workflow():
    # Setup
    topics = load_fixture("topics.json")
    exams = {"Physics": date(2026, 2, 21)}
    
    # Execute
    plan = planner_agent.generate_plan(topics, exams)
    result = verifier_agent.verify(plan, topics)
    
    # Assert
    assert result.valid
    assert all(t.id in plan.all_topic_ids() for t in topics)
```

### End-to-end tests

```python
def test_full_workflow():
    # Place test PDF
    shutil.copy("fixtures/physics.pdf", "storage/uploads/")
    
    # Simulate user
    root_agent.handle_message("I added a physics textbook. Exam is Feb 21.")
    
    # Verify artifacts created
    assert list(Path("storage/state/extracted_text").glob("*.json")) or Path("storage/state/chunks/chunks.jsonl").exists()
    assert list(Path("storage/state/plans").glob("*.md"))
```

---

## Security Considerations

### Local-only design

- No network calls except to Google API (for LLM)
- No file uploads to cloud
- All data stays on disk

### API key management

```bash
# .env
GOOGLE_API_KEY=your_key_here  # Never commit this!
```

```python
# Load safely
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not set")
```

---

## Future Enhancements

1. **Spaced repetition** — Ebbinghaus curve for review scheduling
2. **Progress tracking** — Mark topics as complete, adjust plan
3. **Multi-modal** — Images, diagrams, equations
4. **Collaborative** — Share plans, export to calendar
5. **Adaptive difficulty** — Adjust effort estimates based on user performance

---

## References

- [Google Agent Development Kit (ADK)](https://developers.google.com/adk)
- [Google's Agent Architecture Guide](https://developers.google.com/adk/guides/agents)
- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [LangChain Agent Patterns](https://python.langchain.com/docs/modules/agents/)
