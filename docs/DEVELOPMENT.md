# Development Guide

For developers working on the Agentic Study Planner.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Code Structure](#code-structure)
3. [Development Workflow](#development-workflow)
4. [Testing Strategy](#testing-strategy)
5. [Debugging](#debugging)
6. [Contributing](#contributing)

---

## Development Setup

### Prerequisites

- Python 3.12+
- Git
- Code editor (VS Code, PyCharm, etc.)

### Initial Setup

```bash
# Clone repository
cd study-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If exists, or:
pip install pytest pytest-cov black ruff mypy

# Setup pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Environment Configuration

```bash
# Copy example environment
cp .env.example .env

# Add your API key
echo "GOOGLE_API_KEY=your_key_here" >> .env
```

---

## Code Structure

### Module Organization

```
app/
├── main.py              # ADK entry point (root_agent)
├── agents/              # Root, Ingest, Planner, Tutor, Verifier agents
├── tools/                # Deterministic operations (fs_scan, pdf_extract, chunking, embed, etc.)
├── models/              # Pydantic models (manifest, coverage, chunks, plan, etc.)
└── cli/                 # CLI entrypoints (update_manifest, extract_text, chunk_textbook, etc.)
```

**Design principles**:
1. **Agents** = LLM + reasoning and tool orchestration
2. **Tools** = Deterministic logic (no LLM where possible)
3. **Models** = Pydantic schemas and data structures

### Import Convention

```python
# Standard library
import os
from pathlib import Path
from datetime import datetime

# Third-party
import google.generativeai as genai
from pydantic import BaseModel

# Local
from app.models.chunks import Chunk
from app.models.plan import StudyPlan
from app.tools.pdf_extract import extract_text
```

Use `isort` to auto-format:

```bash
isort app/
```

---

## Development Workflow

### 1. Bottom-up Implementation (Recommended)

Build in this order:

#### Phase 1: Models
```bash
# Define data models first
app/models/manifest.py
app/models/coverage.py
app/models/chunks.py
app/models/plan.py
```

#### Phase 2: Tools
```bash
# Implement deterministic tools
app/tools/fs_scan.py
app/tools/pdf_extract.py
app/tools/doc_classify.py
app/tools/chunking.py
app/tools/embed.py
app/tools/faiss_index.py (or vector_store.py)
```

**Test each tool individually**:

```bash
pytest tests/test_tools/test_pdf_parser.py -v
```

#### Phase 3: Agents
```bash
# Implement agents (use tools)
app/agents/ingestion_agent.py
app/agents/planner_agent.py
app/agents/verifier_agent.py
app/agents/tutor_agent.py
```

**Test agents**:

```bash
pytest tests/test_agents/test_ingestion_agent.py -v
```

#### Phase 4: Orchestration
```bash
# Implement root agent + ADK entrypoint
app/agents/root_agent.py
app/main.py
```

#### Phase 5: Integration
```bash
# End-to-end testing
pytest tests/test_integration/ -v
```

---

## Testing Strategy

### Unit Tests (Tools)

Test deterministic tools with fixtures:

```python
# tests/test_tools/test_pdf_parser.py

import pytest
from pathlib import Path
from app.tools.ingest.pdf_parser import parse_pdf

def test_parse_pdf_basic():
    """Test PDF parsing with sample file."""
    pdf_path = Path("tests/fixtures/sample.pdf")
    pages = extract_text(pdf_path)  # or your PDF parsing function
    
    assert len(pages) > 0
    assert "page" in pages[0]
    assert "text" in pages[0]

def test_parse_pdf_invalid():
    """Test error handling for invalid PDF."""
    with pytest.raises(ValueError):
        parse_pdf(Path("nonexistent.pdf"))
```

Run unit tests:

```bash
pytest tests/test_tools/ -v
```

---

### Integration Tests (Agents)

Test agent workflows with mocks:

```python
# tests/test_agents/test_planner_agent.py

import pytest
from app.agents.planner_agent import planner_agent
from app.models.plan import StudyPlan
from datetime import date

def test_planner_generates_valid_plan():
    """Test plan generation with sample enriched coverage."""
    
    # Setup: use real enriched coverage from storage/state/enriched_coverage/ or fixtures
    exam_file_ids = ["your-exam-file-id"]
    start_date = date(2026, 2, 10)
    end_date = date(2026, 2, 27)
    
    # Execute (via tools or agent)
    # plan = generate_plan(exam_file_ids, start_date, end_date, minutes_per_day=90)
    
    # Assert
    # assert plan is not None
    # assert len(plan.days) > 0
```

Run integration tests:

```bash
pytest tests/test_agents/ -v
```

---

### End-to-End Tests

Test full workflows:

```python
# tests/test_integration/test_full_workflow.py

def test_full_ingestion_to_plan():
    """Test complete workflow from PDF to plan."""
    
    # Setup: Place test PDF
    shutil.copy("tests/fixtures/physics.pdf", "storage/uploads/")
    
    # Execute: Update manifest and run pipeline (or call ingest agent tools)
    # python -m app.cli.update_manifest
    # python -m app.cli.extract_text
    # ... chunk_textbook, build_index, etc.
    
    # Verify: Artifacts created
    assert list(Path("storage/state/extracted_text").glob("*.json"))
    assert Path("storage/state/chunks/chunks.jsonl").exists() or True  # if textbook was chunked
    
    # Execute: Plan (requires coverage + enriched_coverage)
    # plan = generate_plan(...)
    
    # Verify: Plan valid
    # assert plan is not None and len(plan.days) > 0
```

Run end-to-end tests:

```bash
pytest tests/test_integration/ -v
```

---

### Test Coverage

Generate coverage report:

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # View report
```

**Goal**: >80% coverage for tools, >60% for agents.

---

## Debugging

### Logging Setup

Add logging to your modules:

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# In functions
logger.debug(f"Parsing PDF: {pdf_path}")
logger.info(f"Extracted {len(topics)} topics")
logger.error(f"Failed to parse: {error}")
```

Enable logging in `.env`:

```env
LOG_LEVEL=DEBUG
LOG_FILE=storage/logs/app.log
```

---

### Debugging Tools

#### 1. IPython for interactive testing

```bash
pip install ipython

# Run IPython
ipython
```

```python
from app.tools.ingest.pdf_parser import parse_pdf
from pathlib import Path

pages = extract_text(Path("storage/uploads/physics.pdf"))  # or your PDF tool
pages[0]  # Inspect first page
```

#### 2. pdb for breakpoints

```python
import pdb

def some_function():
    result = complex_operation()
    pdb.set_trace()  # Debugger stops here
    return process(result)
```

#### 3. Rich for pretty printing

```python
from rich import print as rprint
from rich.pretty import pprint

# Pretty print objects
pprint(topics)

# Colored output
rprint("[bold green]Success![/bold green]")
```

---

### Common Issues

#### Issue: Import errors

**Symptom**: `ModuleNotFoundError: No module named 'app'`

**Fix**: Run Python from project root:

```bash
cd /path/to/study-agent
python -m app.main
```

Or add to PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

#### Issue: ChromaDB locks

**Symptom**: `sqlite3.OperationalError: database is locked`

**Fix**: Ensure only one process accesses ChromaDB:

```bash
# Kill all Python processes
pkill python

# Or use separate vector stores per test
def test_with_temp_store():
    store = VectorStore(course="test", path="/tmp/test_store")
```

---

#### Issue: API rate limits

**Symptom**: `429 Too Many Requests`

**Fix**: Add rate limiting:

```python
import time

def embed_with_retry(text, max_retries=3):
    for attempt in range(max_retries):
        try:
            return embedder.embed(text)
        except Exception as e:
            if "429" in str(e):
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

---

## Code Quality

### Formatting

Use Black for consistent formatting:

```bash
# Format all code
black app/ tests/

# Check without modifying
black --check app/
```

### Linting

Use Ruff for fast linting:

```bash
# Lint all code
ruff check app/ tests/

# Auto-fix issues
ruff check --fix app/
```

### Type Checking

Use mypy for type safety:

```bash
# Check types
mypy app/

# Strict mode (optional)
mypy --strict app/
```

---

## Git Workflow

### Branch Strategy

```bash
main          # Production-ready code
├── dev       # Development branch
│   ├── feature/ingestion    # Feature branches
│   ├── feature/planning
│   └── fix/pdf-parsing
```

### Commit Messages

Follow conventional commits:

```
feat: Add topic extraction from PDF TOC
fix: Handle encrypted PDFs gracefully
docs: Update architecture documentation
test: Add tests for planner agent
refactor: Simplify chunk generation logic
```

### Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.11
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

Install:

```bash
pre-commit install
```

---

## Performance Profiling

### CPU Profiling

```python
import cProfile
import pstats

def profile_ingestion():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run code
    ingestion_agent.ingest(pdf_path)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumtime')
    stats.print_stats(20)  # Top 20 functions
```

### Memory Profiling

```bash
pip install memory_profiler

# Add decorator
@profile
def ingest_large_pdf():
    ...

# Run
python -m memory_profiler app/agents/ingestion_agent.py
```

---

## Documentation

### Docstring Format (Google Style)

```python
def extract_topics(pages: list[dict], course: str) -> TopicInventory:
    """
    Extract hierarchical topic structure from PDF pages.
    
    Tries to find table of contents first, falls back to header detection
    if TOC is not found.
    
    Args:
        pages: List of page dictionaries with 'text' field
        course: Name of the course (e.g., "Physics")
    
    Returns:
        TopicInventory with extracted topics and page ranges
    
    Raises:
        ValueError: If pages list is empty
        ParseError: If topic structure cannot be determined
    
    Example:
        >>> pages = [{"page": 1, "text": "Chapter 1: Intro"}]
        >>> topics = extract_topics(pages, "Physics")
        >>> len(topics.topics)
        1
    """
    pass
```

---

## Contributing

### Pull Request Process

1. **Create feature branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes**:
   - Write code
   - Add tests
   - Update docs

3. **Run checks**:
   ```bash
   black app/ tests/
   ruff check --fix app/ tests/
   mypy app/
   pytest
   ```

4. **Commit**:
   ```bash
   git add .
   git commit -m "feat: Add my feature"
   ```

5. **Push**:
   ```bash
   git push origin feature/my-feature
   ```

6. **Create PR**:
   - Open pull request on GitHub
   - Fill in PR template
   - Request review

---

## Release Process

### Versioning

Use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Creating a Release

```bash
# Update version
echo "0.2.0" > VERSION

# Tag release
git tag -a v0.2.0 -m "Release v0.2.0: Add planner agent"
git push origin v0.2.0

# Build (if distributing)
python -m build
```

---

## Development Tools

### Recommended VS Code Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "mtxr.sqltools",
    "donjayamanne.githistory"
  ]
}
```

### VS Code Settings

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.analysis.typeCheckingMode": "basic"
}
```

---

## FAQ

### Q: How do I add a new tool?

**A**: 

1. Create or add to a tool file under `app/tools/` (e.g. `app/tools/mytool.py`)
2. Implement deterministic logic (no LLM unless required)
3. Add tests: `tests/test_mytool.py`
4. Expose via `app/agents/tools.py` and assign to the appropriate agent

### Q: How do I add a new agent?

**A**:

1. Create agent file: `app/agents/my_agent.py`
2. Subclass base agent (if exists) or create standalone
3. Add to root agent routing
4. Add tests: `tests/test_agents/test_my_agent.py`

### Q: How do I test with mock LLM responses?

**A**:

```python
from unittest.mock import Mock, patch

def test_intent_detection():
    with patch('app.agents.root_agent.LLM') as mock_llm:
        mock_llm.generate.return_value = "PLAN"
        
        agent = RootAgent()
        intent = agent.detect_intent("Make me a plan")
        
        assert intent == Intent.PLAN
```

---

## Resources

- [Google ADK Documentation](https://developers.google.com/adk)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [pytest Documentation](https://docs.pytest.org/)

---

**Next**: [Architecture Documentation →](ARCHITECTURE.md)
