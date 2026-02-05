# Application Code Structure

Documentation for the `app/` directory.

---

## Overview

The `app/` directory contains all application logic, organized into three layers:

1. **Agents** — Reasoning and orchestration (LLM-powered)
2. **Tools** — Deterministic operations (no LLM calls)
3. **Schemas** — Data models and validation (Pydantic)

---

## Directory Structure

```
app/
├── main.py                    # Entry point (terminal chat loop)
├── state.py                   # Global state management
│
├── agents/                    # Agent implementations
│   ├── __init__.py
│   ├── root_agent.py          # Intent routing, material registry
│   ├── ingestion_agent.py     # PDF → topics → chunks → vectors
│   ├── planner_agent.py       # Topics → study schedule
│   ├── verifier_agent.py      # Coverage + constraint validation
│   └── tutor_agent.py         # RAG-based Q&A
│
├── tools/                     # Deterministic tools
│   ├── __init__.py
│   │
│   ├── ingest/                # Ingestion pipeline
│   │   ├── __init__.py
│   │   ├── pdf_parser.py      # PDF → pages
│   │   ├── topic_extractor.py # Pages → topic inventory
│   │   └── chunker.py         # Pages → chunks
│   │
│   ├── rag/                   # Vector store operations
│   │   ├── __init__.py
│   │   ├── embedder.py        # Text → vectors
│   │   ├── vector_store.py    # ChromaDB wrapper
│   │   └── retriever.py       # Query → relevant chunks
│   │
│   └── planning/              # Scheduling logic
│       ├── __init__.py
│       ├── allocator.py       # Topics → daily schedule
│       └── coverage.py        # Coverage verification
│
└── schemas/                   # Data models
    ├── __init__.py
    ├── topics.py              # Topic, TopicInventory
    ├── plan.py                # StudyPlan, DailySchedule
    └── materials.py           # Material, MaterialRegistry
```

---

## Module Descriptions

### `main.py`

**Purpose**: Entry point for the terminal chat interface.

**Responsibilities**:
- Initialize RootAgent
- Run terminal chat loop
- Handle user input
- Display agent responses

**Key functions**:

```python
def main():
    """Main chat loop."""
    agent = RootAgent()
    
    while True:
        user_input = input("> ")
        
        if user_input == "quit":
            break
        
        response = agent.handle_message(user_input)
        print(response)
```

**Usage**:

```bash
python -m app.main
```

---

### `state.py`

**Purpose**: Global state management (material registry, session state).

**Key classes**:

```python
@dataclass
class Material:
    """Represents a single textbook."""
    course: str
    file_path: Path
    file_hash: str
    ingested: bool
    topic_file: Path
    last_updated: datetime

@dataclass
class MaterialRegistry:
    """Registry of all textbooks."""
    materials: dict[str, Material]
    
    def add_material(self, material: Material) -> None:
        """Add or update a material."""
        self.materials[material.course] = material
    
    def check_for_changes(self) -> list[Action]:
        """Detect new/changed/removed textbooks."""
        ...

@dataclass
class SessionState:
    """Session-specific state."""
    user_constraints: UserConstraints
    current_plan: StudyPlan | None
    plan_valid: bool
    conversation_history: list[Message]
```

---

## Agents

### `agents/root_agent.py`

**Purpose**: Top-level orchestrator.

**Responsibilities**:
- Intent detection (LLM-based)
- Material registry management
- Route to specialized agents

**Key methods**:

```python
class RootAgent:
    def __init__(self):
        self.registry = MaterialRegistry.load()
        self.ingestion_agent = IngestionAgent()
        self.planner_agent = PlannerAgent()
        self.verifier_agent = VerifierAgent()
        self.tutor_agent = TutorAgent()
    
    def handle_message(self, message: str) -> str:
        """Route message to appropriate agent."""
        
        # Check for material changes
        actions = self.registry.check_for_changes()
        if actions:
            return self.handle_material_changes(actions)
        
        # Detect intent
        intent = self.detect_intent(message)
        
        # Route to agent
        if intent == Intent.INGEST:
            return self.ingestion_agent.handle(message)
        elif intent == Intent.PLAN:
            return self.planner_agent.handle(message)
        elif intent == Intent.TUTOR:
            return self.tutor_agent.handle(message)
        ...
```

**Intent detection** (LLM-powered):

```python
def detect_intent(self, message: str) -> Intent:
    """Use LLM to classify user intent."""
    
    prompt = f"""
    Classify this user message:
    "{message}"
    
    Possible intents:
    - INGEST: User mentions adding/changing textbooks
    - PLAN: User requests a study plan
    - TUTOR: User asks for explanation/help
    - STATUS: User asks about current state
    - OTHER: None of the above
    
    Return only the intent name.
    """
    
    response = self.llm.generate(prompt)
    return Intent[response.strip()]
```

---

### `agents/ingestion_agent.py`

**Purpose**: Convert PDFs into structured artifacts.

**Workflow**:

```
PDF → pages → topics → chunks → embeddings → vector store
```

**Key methods**:

```python
class IngestionAgent:
    def ingest(self, pdf_path: Path) -> IngestionResult:
        """Full ingestion pipeline."""
        
        # 1. Parse PDF
        pages = pdf_parser.parse(pdf_path)
        
        # 2. Extract topics
        topics = topic_extractor.extract(pages)
        
        # 3. Chunk text
        chunks = chunker.chunk(pages, topics)
        
        # 4. Generate embeddings
        vectors = embedder.embed_batch(chunks)
        
        # 5. Store in vector DB
        vector_store.store(vectors)
        
        # 6. Save artifacts
        self.save_artifacts(topics, chunks)
        
        return IngestionResult(
            topics=topics,
            chunks=chunks,
            status="success"
        )
```

**Output artifacts**:
- `data/topics/<course>.json`
- `data/chunks/<course>.json`
- `data/indexes/<course>/` (ChromaDB)

---

### `agents/planner_agent.py`

**Purpose**: Generate day-by-day study schedules.

**Inputs**:
- Topic inventories (all courses)
- Exam dates
- User constraints (hours/day)

**Algorithm** (deterministic):

```python
class PlannerAgent:
    def generate_plan(
        self,
        topics: list[Topic],
        exams: dict[str, date],
        constraints: UserConstraints
    ) -> StudyPlan:
        """Generate optimized study schedule."""
        
        # 1. Build date range
        start = datetime.now().date()
        end = max(exams.values())
        days = list(date_range(start, end))
        
        # 2. Estimate effort per topic
        for topic in topics:
            topic.effort_hours = self.estimate_effort(topic)
        
        # 3. Allocate topics to days
        schedule = {}
        remaining_topics = topics.copy()
        
        for day in days:
            # Get topics eligible for this day
            eligible = [
                t for t in remaining_topics
                if exams[t.course] >= day
            ]
            
            # Allocate up to daily capacity
            daily_topics = []
            capacity = constraints.hours_per_day
            
            for topic in eligible:
                if capacity >= topic.effort_hours:
                    daily_topics.append(topic)
                    capacity -= topic.effort_hours
                    remaining_topics.remove(topic)
            
            schedule[day] = daily_topics
        
        return StudyPlan(schedule=schedule)
```

**Output**:
- `data/plans/study_plan.md`

---

### `agents/verifier_agent.py`

**Purpose**: Validate study plans (coverage, constraints).

**Checks**:

```python
class VerifierAgent:
    def verify(
        self,
        plan: StudyPlan,
        topics: list[Topic],
        exams: dict[str, date]
    ) -> VerificationResult:
        """Verify plan meets all requirements."""
        
        errors = []
        
        # Check 1: Coverage (100%)
        scheduled = set(plan.all_topic_ids())
        required = set(t.id for t in topics)
        uncovered = required - scheduled
        
        if uncovered:
            errors.append(f"Uncovered topics: {uncovered}")
        
        # Check 2: Deadline compliance
        for day, day_topics in plan.schedule.items():
            for topic in day_topics:
                exam_date = exams[topic.course]
                if day > exam_date:
                    errors.append(
                        f"Topic {topic.id} scheduled after exam"
                    )
        
        # Check 3: Workload limits
        for day, day_topics in plan.schedule.items():
            total = sum(t.effort_hours for t in day_topics)
            if total > MAX_HOURS_PER_DAY:
                errors.append(f"Day {day} overloaded: {total}h")
        
        return VerificationResult(
            valid=(len(errors) == 0),
            errors=errors
        )
```

**Feedback loop**:

```python
# In PlannerAgent:
def generate_with_verification(self, ...) -> StudyPlan:
    """Generate and verify in a loop."""
    
    max_attempts = 3
    for attempt in range(max_attempts):
        plan = self.generate_plan(...)
        result = verifier_agent.verify(plan, topics, exams)
        
        if result.valid:
            return plan
        
        # Adjust constraints based on errors
        self.adjust_constraints(result.errors)
    
    raise PlanningError("Could not generate valid plan")
```

---

### `agents/tutor_agent.py`

**Purpose**: Answer questions using RAG.

**Workflow**:

```
User query → embed → retrieve chunks → generate answer with citations
```

**Key methods**:

```python
class TutorAgent:
    def answer_question(self, question: str) -> str:
        """Generate grounded answer to user question."""
        
        # 1. Embed query
        query_vector = embedder.embed(question)
        
        # 2. Retrieve relevant chunks
        chunks = retriever.retrieve(
            query_vector,
            top_k=5,
            min_similarity=0.7
        )
        
        # 3. Build context from chunks
        context = self.build_context(chunks)
        
        # 4. Generate answer with citations
        prompt = f"""
        Answer this question using ONLY the provided context.
        Always cite page numbers.
        
        Question: {question}
        
        Context:
        {context}
        
        Format:
        - Direct answer
        - Citations (e.g., "Physics textbook, pp. 12-15")
        - Example if helpful
        """
        
        answer = self.llm.generate(prompt)
        
        return answer
```

**Citation formatting**:

```python
def build_context(self, chunks: list[Chunk]) -> str:
    """Format chunks with metadata for LLM."""
    
    context = []
    for chunk in chunks:
        context.append(
            f"[{chunk.course}, pp. {chunk.pages}]\n"
            f"{chunk.text}\n"
        )
    
    return "\n---\n".join(context)
```

---

## Tools

### `tools/ingest/pdf_parser.py`

**Purpose**: Extract text from PDFs.

**Key function**:

```python
def parse_pdf(pdf_path: Path) -> list[dict]:
    """
    Parse PDF into structured pages.
    
    Returns:
        [{"page": 1, "text": "...", "metadata": {...}}, ...]
    """
    
    import fitz  # PyMuPDF
    
    doc = fitz.open(pdf_path)
    pages = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        pages.append({
            "page": page_num + 1,
            "text": text,
            "metadata": {
                "width": page.rect.width,
                "height": page.rect.height
            }
        })
    
    return pages
```

**Alternative**: Use `pdfplumber` for tables.

---

### `tools/ingest/topic_extractor.py`

**Purpose**: Extract hierarchical topic structure.

**Strategy**:
1. Find table of contents
2. Parse chapter/section headers
3. Build topic tree
4. Assign unique IDs

**Key function**:

```python
def extract_topics(pages: list[dict]) -> TopicInventory:
    """
    Extract topics from parsed pages.
    
    Returns:
        TopicInventory with hierarchical structure
    """
    
    # Try to find TOC first
    toc_pages = detect_toc(pages)
    
    if toc_pages:
        topics = parse_toc(toc_pages)
    else:
        # Fallback: detect headers by font/style
        topics = detect_headers_by_style(pages)
    
    # Assign IDs
    assign_topic_ids(topics, prefix="phys")
    
    return TopicInventory(
        course="Physics",
        topics=topics
    )
```

---

### `tools/ingest/chunker.py`

**Purpose**: Split text into overlapping chunks.

**Key function**:

```python
def chunk_text(
    pages: list[dict],
    topics: TopicInventory,
    chunk_size: int = 512,
    overlap: int = 128
) -> list[Chunk]:
    """
    Chunk text with topic metadata.
    
    Returns:
        List of chunks with topic_id, page_range, text
    """
    
    chunks = []
    chunk_id = 0
    
    for topic in topics.all_topics():
        # Get pages for this topic
        topic_pages = [
            p for p in pages
            if topic.page_range[0] <= p["page"] <= topic.page_range[1]
        ]
        
        # Combine text
        text = "\n".join(p["text"] for p in topic_pages)
        
        # Split into chunks
        for i in range(0, len(text), chunk_size - overlap):
            chunk_text = text[i:i + chunk_size]
            
            chunks.append(Chunk(
                chunk_id=f"c_{chunk_id:04d}",
                topic_id=topic.topic_id,
                text=chunk_text,
                pages=[p["page"] for p in topic_pages]
            ))
            
            chunk_id += 1
    
    return chunks
```

---

### `tools/rag/embedder.py`

**Purpose**: Generate embeddings for text.

**Key function**:

```python
def embed_batch(
    texts: list[str],
    batch_size: int = 50
) -> list[list[float]]:
    """
    Generate embeddings in batches.
    
    Uses Google's embedding model (models/embedding-001).
    """
    
    import google.generativeai as genai
    
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        # Call embedding API
        result = genai.embed_content(
            model="models/embedding-001",
            content=batch
        )
        
        embeddings.extend(result["embedding"])
    
    return embeddings
```

---

### `tools/rag/vector_store.py`

**Purpose**: ChromaDB wrapper.

**Key class**:

```python
class VectorStore:
    def __init__(self, course: str):
        import chromadb
        
        self.client = chromadb.PersistentClient(
            path=f"data/indexes/{course}"
        )
        self.collection = self.client.get_or_create_collection(course)
    
    def store(self, chunks: list[Chunk], embeddings: list[list[float]]):
        """Store chunks with embeddings."""
        
        self.collection.add(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "topic_id": c.topic_id,
                    "pages": ",".join(map(str, c.pages))
                }
                for c in chunks
            ]
        )
    
    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5
    ) -> list[dict]:
        """Retrieve similar chunks."""
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        return results
```

---

### `tools/planning/allocator.py`

**Purpose**: Deterministic scheduling algorithm.

**Key function**:

```python
def allocate_topics(
    topics: list[Topic],
    exams: dict[str, date],
    hours_per_day: float
) -> dict[date, list[Topic]]:
    """
    Allocate topics to days.
    
    Strategy:
    - Earliest deadline first (EDF)
    - Greedy packing within daily capacity
    """
    
    schedule = {}
    
    # Sort topics by exam deadline
    sorted_topics = sorted(
        topics,
        key=lambda t: exams[t.course]
    )
    
    # Allocate
    current_date = datetime.now().date()
    
    for topic in sorted_topics:
        exam_date = exams[topic.course]
        
        # Find first available day with capacity
        for day in date_range(current_date, exam_date):
            if day not in schedule:
                schedule[day] = []
            
            daily_effort = sum(t.effort_hours for t in schedule[day])
            
            if daily_effort + topic.effort_hours <= hours_per_day:
                schedule[day].append(topic)
                break
    
    return schedule
```

---

## Schemas

### `schemas/topics.py`

```python
from pydantic import BaseModel
from typing import Optional

class Topic(BaseModel):
    topic_id: str
    title: str
    page_range: tuple[int, int]
    subtopics: list['Topic'] = []
    effort_hours: Optional[float] = None

class TopicInventory(BaseModel):
    course: str
    topics: list[Topic]
    
    def all_topics(self) -> list[Topic]:
        """Flatten topic tree."""
        result = []
        for topic in self.topics:
            result.append(topic)
            result.extend(topic.subtopics)
        return result
```

---

### `schemas/plan.py`

```python
from pydantic import BaseModel
from datetime import date

class DailySchedule(BaseModel):
    date: date
    topics: list[Topic]
    total_hours: float

class StudyPlan(BaseModel):
    schedule: dict[date, list[Topic]]
    
    def all_topic_ids(self) -> set[str]:
        """Get all scheduled topic IDs."""
        return {
            t.topic_id
            for topics in self.schedule.values()
            for t in topics
        }
```

---

## Testing

Each module should have corresponding tests in `tests/`:

```
tests/
├── test_agents/
│   ├── test_root_agent.py
│   ├── test_planner_agent.py
│   └── ...
├── test_tools/
│   ├── test_pdf_parser.py
│   ├── test_chunker.py
│   └── ...
└── test_integration/
    └── test_full_workflow.py
```

---

## Code Style

- **Type hints**: Required for all functions
- **Docstrings**: Google-style for all public functions
- **Formatting**: Black (line length 88)
- **Linting**: Ruff
- **Imports**: isort

---

## Next Steps

1. Implement tools first (bottom-up)
2. Then implement agents (top-down)
3. Finally, integrate in `main.py`

See [ARCHITECTURE.md](../docs/ARCHITECTURE.md) for design details.
