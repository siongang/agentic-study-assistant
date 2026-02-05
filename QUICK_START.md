# Quick Start Guide

Get the Agentic Study Planner running in 5 minutes.

---

## Step 1: Setup (2 minutes)

```bash
# Navigate to project
cd study-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

---

## Step 2: Add Textbooks (1 minute)

```bash
# Place your PDF textbooks here
cp ~/Downloads/physics.pdf data/uploads/
cp ~/Downloads/biology.pdf data/uploads/
```

---

## Step 3: Run (2 minutes)

```bash
python -m app.main
```

**Example conversation**:

```
> I added physics and biology textbooks.
> Physics exam is Feb 21, biology exam is Feb 25.
> I can study 3 hours per day.
> Make me a study plan.

[Agent ingests textbooks and generates plan...]

✓ Plan saved to data/plans/study_plan.md
```

---

## Step 4: View Your Plan

```bash
cat data/plans/study_plan.md
```

---

## Commands

| Command | Description |
|---------|-------------|
| `status` | Show materials and plan |
| `help` | List available commands |
| `quit` | Exit chat |

---

## Next Steps

- **Read the docs**: [`docs/USAGE.md`](docs/USAGE.md) for detailed usage
- **Understand the system**: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for design
- **Develop**: [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for contributing

---

## Troubleshooting

**Issue**: "GOOGLE_API_KEY not set"

```bash
# Make sure .env exists and contains:
GOOGLE_API_KEY=your_actual_key_here
```

**Issue**: "No textbooks found"

```bash
# Check files are in the right place:
ls data/uploads/
# Should show your PDFs
```

**Issue**: Import errors

```bash
# Make sure virtual environment is activated:
which python  # Should show .venv/bin/python
```

---

## What This System Does

1. **Ingests** your textbooks (PDFs) and extracts topics
2. **Generates** a day-by-day study plan with 100% topic coverage
3. **Acts as a tutor** to answer questions about your material
4. **Automatically updates** when you add/change textbooks

All local, no cloud storage required.

---

**Full documentation**: [README.md](README.md)
