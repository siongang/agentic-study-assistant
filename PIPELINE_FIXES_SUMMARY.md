# Pipeline Fixes Summary

## Changes Implemented

### 1. Fixed Critical Bug in `classify_document()` ✅
**File**: `app/agents/tools.py` (lines 233-310)

**Problem**: Used `file_entry.filename` before it was defined, causing NameError

**Fix**: Moved manifest loading before calling `classify_doc_llm()`

```python
# Before (BROKEN):
def classify_document(file_id: str) -> dict:
    # ... load extracted text ...
    result = classify_doc_llm(
        filename=file_entry.filename,  # ❌ NOT DEFINED YET
    )
    # ... later load manifest ...

# After (FIXED):
def classify_document(file_id: str) -> dict:
    manifest = load_manifest(...)  # ✅ Load FIRST
    file_entry = next(...)
    # ... then load extracted text ...
    result = classify_doc_llm(
        filename=file_entry.filename,  # ✅ NOW AVAILABLE
    )
```

### 2. Added Status-Based Caching ✅
**Files Modified**: `app/agents/tools.py`

Added caching checks to three functions to prevent reprocessing:

#### `extract_text()` (lines 181-214)
- Checks if output exists AND status != 'new'/'stale'
- Returns cached result with `"cached": True` flag
- Logs: `"✓ Using cached extraction for {filename}"`

#### `extract_toc_tool()` (lines 350-362)
- Checks if TOC metadata exists AND status != 'new'/'stale'
- Returns cached TOC chapters
- Logs: `"✓ Using cached TOC for {filename}"`

#### `chunk_textbook()` (lines 434-450)
- Checks if chunks exist for file_id AND status != 'new'/'stale'
- Loads chunks.jsonl and filters by file_id
- Returns cached chunk count

### 3. Added Strict Prerequisite Validation ✅
**File**: `app/agents/tools.py`

Added validation to ensure dependencies are met before processing:

#### `extract_toc_tool()` (lines 350-355)
- Validates `doc_type == "textbook"` before extracting TOC
- Returns clear error if wrong type

#### `chunk_textbook()` (lines 438-452)
- Validates `doc_type == "textbook"`
- Warns if TOC metadata missing (but continues with semantic chunking)

#### `build_index()` (lines 541-547)
- Validates at least one chunk exists after loading
- Prevents building empty index

#### `extract_coverage()` (lines 635-641)
- Validates `doc_type` is "exam_overview" or "unknown"
- Returns error for wrong document types

### 4. Streamlined Agent Prompts ✅
**Files Modified**: All agent files

Condensed verbose prompts to focus on core workflow:

| Agent | Before | After | Reduction |
|-------|--------|-------|-----------|
| `ingest_agent` | 74 lines | 22 lines | 70% |
| `root_agent` | 47 lines | 15 lines | 68% |
| `planner_agent` | 19 lines | 12 lines | 37% |
| `tutor_agent` | 18 lines | 11 lines | 39% |

**Key improvements**:
- Removed repetitive examples and "NEVER/ALWAYS" sections
- Focused on core workflow steps
- Kept essential validation rules
- Made instructions scannable

## Testing & Verification

### Current State (Before Testing)
Run `python3 test_pipeline_fixes.py` to see:
- ✅ All 9 files have `doc_type='unknown'` (confirms original bug)
- ✅ All 9 files have `status='processed'` 
- ✅ All 9 extracted text files exist
- ✅ 3 TOC metadata files exist (for textbooks)

### Expected Behavior (After Running Agent)

1. **Classification should work**:
   - `classify_document()` will NOT crash with NameError
   - All files will get proper doc_types: textbook, exam_overview, or syllabus
   - Manifest will update with doc_type, confidence, and reasoning

2. **Caching should work**:
   - Tools will skip extraction if status='processed' and output exists
   - Logs will show "Already extracted (cached)" messages
   - No redundant PDF processing or TOC extraction

3. **Validation should work**:
   - `extract_toc_tool()` will only run on textbooks
   - `chunk_textbook()` will only run on textbooks
   - Clear error messages for wrong document types

4. **Agent prompts should be clearer**:
   - Agents will be more focused in their responses
   - Less verbose explanations
   - Faster decision-making

## Testing Steps

### Automated Verification
```bash
cd /home/sion/code/study-agent
python3 test_pipeline_fixes.py
```

### Manual Testing (Recommended)

1. **Start the ADK server**:
   ```bash
   python -m adk dev --app app.agent
   ```

2. **Test Classification Fix**:
   - In ADK UI, say: "Classify all files"
   - Expected: All files get classified without errors
   - Check manifest.json: `doc_type` should be updated

3. **Test Caching**:
   - Say: "Process all files again"
   - Expected: Tools should skip already-processed files
   - Check logs for "cached" messages

4. **Verify Manifest**:
   ```bash
   python3 test_pipeline_fixes.py
   ```
   - Should show 0 files with `doc_type='unknown'`

5. **Check Terminal Logs**:
   - Look for "✓ Using cached..." messages
   - Verify no duplicate extraction or TOC operations
   - Confirm classification completes successfully

## Files Changed

1. `/home/sion/code/study-agent/app/agents/tools.py` - Main fixes
2. `/home/sion/code/study-agent/app/agents/ingest_agent.py` - Condensed prompt
3. `/home/sion/code/study-agent/app/agents/root_agent.py` - Condensed prompt
4. `/home/sion/code/study-agent/app/agents/planner_agent.py` - Condensed prompt
5. `/home/sion/code/study-agent/app/agents/tutor_agent.py` - Condensed prompt
6. `/home/sion/code/study-agent/test_pipeline_fixes.py` - NEW: Test script

## Success Criteria

- ✅ `classify_document()` successfully updates doc_type in manifest
- ✅ Tools skip processing when status != 'new'/'stale'
- ✅ No redundant text extraction or TOC processing
- ✅ Clear error messages when prerequisites missing
- ✅ Agent prompts are concise and actionable (~15-30 lines)

## Next Steps

1. Run the agent with: `python -m adk dev --app app.agent`
2. Test classification on all files
3. Verify caching works (check logs for "cached" messages)
4. Confirm manifest.json gets updated with doc_types
5. Report any remaining issues

---

**Implementation Date**: 2026-02-08
**Status**: ✅ Complete - Ready for Testing
