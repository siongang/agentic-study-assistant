# Agent System Quickstart

## 🎉 What We Just Built

You now have a complete **4-agent system** for study planning:

### The Agents

1. **Ingest Agent 📥** - Processes files (PDF → text → chunks → FAISS)
2. **Planner Agent 📅** - Creates study schedules with RAG enrichment
3. **Tutor Agent 🎓** - Answers questions using textbook search
4. **Root Agent 🎯** - Orchestrates everything and manages user interaction

### The Tools

Created **14 ADK tool wrappers** that wrap your existing CLI commands:

- 6 tools for Ingest Agent
- 6 tools for Planner Agent  
- 2 tools for Tutor Agent
- 3 tools for Root Agent (+ access to all sub-agents)

---

## 🚀 Installation & Setup

### 1. Install Dependencies

```bash
cd /home/sion/code/study-agent

# Install all requirements (including google-adk)
pip install -r requirements.txt

# Or install individually if needed
pip install google-adk google-genai
```

### 2. Verify Installation

```bash
# Test imports
python3 -c "from app.agents.root_agent import root_agent; print('✅ Import successful!')"

# Should see: ✅ Import successful!
```

### 3. Set Environment Variables

Make sure `.env` has your API keys:

```bash
# .env
GOOGLE_API_KEY=your_gemini_api_key_here
# OR
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🎮 Running the Agent System

### Option 1: CLI Chat (Recommended for testing)

```bash
adk run
```

This launches an interactive terminal chat with the root agent.

### Option 2: Web UI

```bash
adk web
```

Opens a browser-based chat interface.

### Option 3: API Server

```bash
adk api_server
```

Runs a REST API server for programmatic access.

---

## 💬 Example Interactions

### 1. Processing Files

```
You: I just uploaded a textbook and exam overview

Agent: [Auto-syncs] Found 2 new files! Let me process them...
       [Delegates to Ingest Agent]
       - Extracted text from textbook (324 pages)
       - Classified as textbook
       - Extracted 12 chapters
       - Created 245 chunks
       - Built FAISS index
       ✅ Your materials are ready!
```

### 2. Creating a Study Plan

```
You: Create a study plan for my midterm

Agent: [Checks readiness]
       I found 1 exam ready for planning:
       - Midterm Examination 1 (68 topics)
       
       When does your exam start? And how many minutes per day can you study?

You: Exam is on Feb 27, I can do 90 minutes per day

Agent: [Delegates to Planner Agent]
       [Enriching coverage with textbook evidence...]
       [Generating schedule...]
       
       ✅ Created 18-day study plan:
       - 68 topics across 6 chapters
       - 38.5 total hours
       - Strategy: balanced
       - Includes reading pages, practice problems, and study questions
       
       Would you like me to export this to markdown or CSV?
```

### 3. Asking Questions

```
You: What is statistical significance?

Agent: [Delegates to Tutor Agent]
       [Searching textbook...]
       
       Statistical significance refers to a result that is unlikely to occur by 
       chance alone. According to your textbook (pages 25-27), a result is 
       considered statistically significant if:
       
       1. The probability of it occurring by chance is very small (typically < 5%)
       2. It passes a hypothesis test with a predetermined significance level
       3. The p-value is less than alpha (usually 0.05)
       
       The textbook distinguishes this from *practical significance*, which asks 
       whether the result is large enough to matter in the real world.
       
       See also: pages 28-29 for examples in drug trials
       
       Would you like me to explain the difference between statistical and 
       practical significance in more detail?
```

---

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'google'"

**Solution:**
```bash
pip install google-genai google-adk
```

### "FAISS index not found"

**Solution:**
```bash
# In ADK chat, tell the agent:
"Process my files and build the index"

# Or run CLI directly:
python -m app.cli.build_index
```

### "Enriched coverage not found"

**Solution:**
```bash
# In ADK chat:
"Enrich coverage for my exam"

# Or CLI:
python -m app.cli.enrich_coverage <file_id>
```

### Agent doesn't respond

**Check:**
1. API key is set in `.env`
2. Files are uploaded to `uploads/` directory
3. Run `sync_files()` tool manually

---

## 📊 System Status Check

```python
# Quick Python script to check status
from app.agents.tools import list_available_exams, check_readiness

# See what exams are ready
result = list_available_exams()
print(result)

# Check if ready for planning
result = check_readiness("create_plan", exam_file_ids=["your-exam-id"])
print(result)
```

---

## 🎯 Agent Capabilities Summary

### What Root Agent Can Do:
- ✅ Auto-sync files on every turn
- ✅ Route requests to specialist agents
- ✅ Check system readiness
- ✅ Provide clear error messages
- ✅ Guide users through full workflow

### What Ingest Agent Can Do:
- ✅ Scan uploads directory
- ✅ Extract text from PDFs
- ✅ Classify documents automatically
- ✅ Extract textbook table of contents
- ✅ Chunk textbooks intelligently
- ✅ Build searchable FAISS index

### What Planner Agent Can Do:
- ✅ Extract exam coverage from PDFs
- ✅ Enrich objectives with textbook evidence (RAG)
- ✅ Generate balanced study schedules
- ✅ Create study questions from textbook
- ✅ Export plans to MD/CSV/JSON
- ✅ Support multiple scheduling strategies

### What Tutor Agent Can Do:
- ✅ Search textbook semantically
- ✅ Answer questions with page citations
- ✅ Filter by exam scope
- ✅ Never hallucinate (grounded in chunks)
- ✅ Suggest related concepts

---

## 📁 File Structure

```
app/
├── agents/
│   ├── tools.py              # All 14 tool wrappers
│   ├── ingest_agent.py       # Data pipeline
│   ├── planner_agent.py      # Schedule generation
│   ├── tutor_agent.py        # Q&A system
│   └── root_agent.py         # Orchestrator
├── main.py                   # ADK entrypoint
├── cli/                      # Standalone CLI commands (still work)
├── tools/                    # Core logic (used by tool wrappers)
└── models/                   # Pydantic models

docs/
├── AGENT_ARCHITECTURE.md     # Full technical spec
├── AGENT_PROCESSES.md        # Process flows
├── AGENT_IMPLEMENTATION_STATUS.md  # Implementation checklist
└── AGENT_QUICKSTART.md       # This file
```

---

## 🧪 Testing Your Agents

### Manual Test Flow:

```bash
# 1. Start ADK
adk run

# 2. Test Ingest
You: "Process my uploaded files"

# 3. Test Planner
You: "Create a study plan for my exam starting Feb 10"

# 4. Test Tutor
You: "What is a confidence interval?"

# 5. Test Export
You: "Export my plan to markdown"
```

### Automated Test (Python):

```python
from app.agents.tools import (
    sync_files,
    extract_text,
    classify_document,
    build_index,
    extract_coverage,
    enrich_coverage_tool,
    generate_plan,
    search_textbook,
    list_available_exams
)

# Test sync
print("Testing sync...")
result = sync_files()
assert result["status"] == "success"

# Test list exams
print("Testing list exams...")
result = list_available_exams()
print(f"Found {len(result['exams'])} exams")

# More tests...
```

---

## 🎓 Next Steps

1. **Install ADK** - Run `pip install -r requirements.txt`
2. **Test Launch** - Run `adk run` and try chatting
3. **Upload Files** - Add PDFs to `uploads/` directory
4. **Process Files** - Tell agent to process them
5. **Create Plan** - Generate your first study schedule
6. **Ask Questions** - Test the tutoring functionality

---

## 💡 Tips

- **Auto-sync works**: Root agent syncs files automatically
- **Be specific**: "Create a plan for exam X starting Y" works better than "help me study"
- **Check status**: Ask "What exams do you have?" to see what's ready
- **Errors are helpful**: If something fails, the agent explains what's missing
- **Tools are composable**: Root agent can chain multiple operations

---

## 🚨 Known Limitations

- **No web search**: Only uses uploaded materials
- **No external APIs**: Pure local RAG system
- **No OCR**: PDFs must have extractable text
- **Single textbook**: Currently assumes one textbook per exam (can extend)
- **English only**: No multilingual support yet

---

## 📚 Documentation

- **Full Architecture**: `docs/AGENT_ARCHITECTURE.md`
- **Process Flows**: `docs/AGENT_PROCESSES.md`
- **Implementation Status**: `docs/AGENT_IMPLEMENTATION_STATUS.md`
- **Original Execution Plan**: `docs/EXECUTION_PLAN.md`

---

## ✨ What Makes This System Special

1. **Autonomous Agents**: Each agent is a specialist
2. **RAG-Powered**: All recommendations grounded in textbook
3. **No Hallucination**: Only uses retrieved content
4. **Auto-Sync**: System stays up-to-date automatically
5. **Clear Errors**: Always explains what's missing
6. **Composable**: Agents work together seamlessly
7. **Local-First**: No external dependencies (except Gemini API)

---

**Ready to roll!** 🚀

Run `pip install -r requirements.txt && adk run` to get started.
