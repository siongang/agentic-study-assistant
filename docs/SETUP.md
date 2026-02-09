# Setup Guide

Complete installation and configuration instructions for the Agentic Study Planner.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Python**: 3.12 or higher
- **OS**: Linux, macOS, or Windows (WSL recommended)
- **Disk Space**: ~2GB for dependencies + vector indexes
- **RAM**: Minimum 4GB (8GB recommended)

### Google API Key

You'll need a Google API key for Gemini models:

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)

**Note**: Keep this key secret! Never commit it to git.

---

## Installation

### 1. Clone or navigate to the repository

```bash
cd study-agent
```

### 2. Create a virtual environment

**On Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows (Command Prompt):**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**On Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**On Windows (WSL):**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

### 3. Upgrade pip (recommended)

```bash
pip install --upgrade pip
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Google ADK and Generative AI SDK
- PDF parsing libraries (PyMuPDF, pdfplumber)
- Vector database (ChromaDB, FAISS)
- Data validation (Pydantic)
- Terminal utilities (rich, tqdm)

**Installation time**: ~2-5 minutes (depending on internet speed)

---

## Configuration

### 1. Create environment file

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Add your API key

Edit `.env` with your favorite editor:

```bash
nano .env   # or vim, code, etc.
```

Add your Google API key:

```env
# .env

# Google AI API Key (required)
GOOGLE_API_KEY=AIzaSy...your_actual_key_here

# Model configuration (optional)
EMBEDDING_MODEL=models/embedding-001
CHAT_MODEL=gemini-2.0-flash

# Vector store configuration (optional)
VECTOR_STORE_PATH=storage/state/index
CHUNK_SIZE=512
CHUNK_OVERLAP=128

# Planning configuration (optional)
DEFAULT_HOURS_PER_DAY=3.0
MAX_HOURS_PER_DAY=8.0
```

**Important**: Make sure `.env` is in `.gitignore` (it should be by default).

### 3. Verify directory structure

The project uses `storage/` for all data. Ensure these exist:

```bash
ls -la storage/
```

Expected layout:

```
storage/
├── uploads/     # Place your PDFs here
├── state/       # manifest.json, extracted_text/, chunks/, index/, coverage/, plans/, etc.
├── logs/        # (optional)
└── topics/      # (optional / reserved)
```

If needed, create the minimal structure:

```bash
mkdir -p storage/uploads storage/state storage/logs
```

---

## Verification

### 1. Test Python environment

```bash
python --version
```

Should show `Python 3.12.x` or higher.

### 2. Test imports

```bash
python -c "import google.generativeai; import chromadb; import fitz; print('✓ All dependencies imported successfully')"
```

If you see the checkmark, you're good!

### 3. Verify API key

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', 'Found ✓' if os.getenv('GOOGLE_API_KEY') else 'MISSING ✗')"
```

Should show: `API Key: Found ✓`

### 4. Run a test script (optional)

Create a quick test:

```bash
python -c "
from dotenv import load_dotenv
import google.generativeai as genai
import os

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Say hello!')
print(response.text)
"
```

You should see a friendly response from Gemini.

---

## Directory Permissions

Ensure the application can read/write to the storage directories:

```bash
chmod -R u+rw storage/
```

---

## Optional: Rich Terminal Output

For prettier terminal output, we use the `rich` library (already in requirements).

Test it:

```bash
python -c "from rich.console import Console; c = Console(); c.print('[bold green]✓ Rich terminal output working![/bold green]')"
```

You should see colored, formatted text.

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'google'`

**Solution**: Make sure the virtual environment is activated:

```bash
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

Then reinstall dependencies:

```bash
pip install -r requirements.txt
```

---

### Issue: `GOOGLE_API_KEY not set`

**Solution**: Check your `.env` file:

```bash
cat .env
```

Make sure it contains:

```env
GOOGLE_API_KEY=AIzaSy...
```

And that you're loading it in your code:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

### Issue: ChromaDB fails to initialize

**Error message**: `sqlite3.OperationalError: attempt to write a readonly database`

**Solution**: Check directory permissions:

```bash
chmod -R u+rw storage/state/index/
```

---

### Issue: PDF parsing fails

**Error message**: `fitz.fitz.FileDataError: cannot open file`

**Possible causes**:
1. PDF is corrupted
2. PDF is encrypted
3. File path is incorrect

**Solution**:

```bash
# Test manually
python -c "import fitz; doc = fitz.open('storage/uploads/your_file.pdf'); print(f'Pages: {len(doc)}')"
```

If this fails, try re-downloading the PDF or using a different PDF tool.

---

### Issue: `ImportError: cannot import name 'embedding-001'`

**Solution**: Update the Google Generative AI library:

```bash
pip install --upgrade google-generativeai
```

---

### Issue: Slow embeddings

**Symptom**: Embedding 100 chunks takes >5 minutes

**Solution**: Use batch embedding:

```python
# Instead of:
for chunk in chunks:
    vector = embed(chunk)

# Do:
vectors = embed_batch(chunks, batch_size=50)
```

This is already implemented in `app/tools/embed.py` (batch embedding).

---

### Issue: Out of memory during PDF parsing

**Symptom**: Python crashes with `MemoryError`

**Solution**: Process PDFs page-by-page instead of loading entirely:

```python
# Already implemented in pdf_parser.py
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    yield {"page": page_num, "text": text}
```

---

### Issue: Windows path issues

**Symptom**: `FileNotFoundError` with paths like `data\uploads\file.pdf`

**Solution**: Use `pathlib.Path` for cross-platform compatibility:

```python
from pathlib import Path

# Instead of:
path = Path("storage") / "uploads" / "file.pdf"

# Use:
path = Path("storage") / "uploads" / "file.pdf"
```

All code in this project uses `pathlib`.

---

## Testing Your Setup

### Minimal End-to-End Test

1. **Place a test PDF** (any PDF, even a 1-page document):

   ```bash
   cp ~/Downloads/sample.pdf storage/uploads/test.pdf
   ```

2. **Update manifest and run extraction**:

   ```bash
   python -m app.cli.update_manifest
   python -m app.cli.extract_text
   ```

3. **Check output**:

   ```bash
   ls storage/state/extracted_text/
   # Should show JSON files per file_id
   ```

---

## Next Steps

Once setup is complete:

1. Read [Agent Quickstart](AGENT_QUICKSTART.md) to run the agent and try example flows
2. Read the [Architecture](ARCHITECTURE.md) to understand how it works
3. Place your PDFs (syllabus, exam overviews, textbooks) in `storage/uploads/`
4. Run `adk web` or `adk run` to start the chat interface (entrypoint: `app.main`)

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | None | Your Google AI API key |
| `EMBEDDING_MODEL` | No | `gemini-embedding-001` | Embedding model to use |
| `CHAT_MODEL` | No | `gemini-2.0-flash` | Chat model for agents |
| `VECTOR_STORE_PATH` | No | `storage/state/index` | Where to store FAISS index and mapping |
| `CHUNK_SIZE` | No | `512` | Tokens per chunk |
| `CHUNK_OVERLAP` | No | `128` | Overlap between chunks |
| `DEFAULT_HOURS_PER_DAY` | No | `3.0` | Default study hours per day |
| `MAX_HOURS_PER_DAY` | No | `8.0` | Maximum study hours per day |

---

## Dependency Tree

For reference, here's what `requirements.txt` installs:

```
google-adk
  ├── google-generativeai
  ├── google-cloud-aiplatform
  └── ... (Google Cloud dependencies)

google-generativeai
  ├── google-auth
  └── protobuf

pymupdf (fitz)
  └── (PDF rendering libraries)

pdfplumber
  ├── pdfminer.six
  └── Pillow

chromadb
  ├── hnswlib
  ├── fastapi
  └── sqlite3

faiss-cpu
  └── numpy

pydantic
  └── typing-extensions

rich
  ├── pygments
  └── markdown-it-py

tqdm
  └── (no dependencies)
```

---

## Uninstallation

To remove the project:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf .venv

# Remove state artifacts (optional)
rm -rf storage/state/extracted_text storage/state/chunks storage/state/index storage/state/plans

# Remove environment file (optional)
rm .env
```

---

## Support

If you encounter issues not covered here:

1. Check the [Architecture documentation](ARCHITECTURE.md) for design details
2. Review [Agent Quickstart](AGENT_QUICKSTART.md) for workflow examples
3. Inspect logs in `storage/logs/` (if logging is enabled)
4. Check the Google ADK documentation: https://developers.google.com/adk

---

**Next**: [Agent Quickstart →](AGENT_QUICKSTART.md)
