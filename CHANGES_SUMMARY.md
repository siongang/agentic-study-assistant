# Question Generation Improvements

## Summary
Replaced broken LLM-based golden questions with **RAG-based study questions** that use actual textbook content. Removed prerequisite checks entirely.

## What Changed

### 1. **Removed: Golden Questions** ❌
- **Problem**: LLM was failing and generating broken fallback questions like:
  - "How would you explain define to someone unfamiliar with the topic?"
  - "How would you explain understand to someone unfamiliar with the topic?"
- **Cause**: Questions were generated WITHOUT textbook context, just from objective text + regex-extracted terms
- **Cost**: 1 LLM call per topic (expensive, useless)

### 2. **Removed: Prerequisite Checks** ✨
- **Before**: Called LLM with topic + chapter + title → generic output
  - "Review Chapter X concepts if you feel uncertain about the foundations."
- **After**: Completely removed (field no longer exists)
- **Reason**: Not useful, added noise, wasted an LLM call
- **Savings**: 1 LLM call per topic saved

### 3. **Added: RAG-Based Study Questions** ⭐
- **New approach**: Generate questions FROM actual textbook excerpts
- **Process**:
  1. RAG Scout already retrieves relevant chunks → Now stores top 2-3 chunk excerpts
  2. Pass chunk text + objective to LLM
  3. LLM generates contextual question based on specific textbook content
- **Result**: Questions that reference actual concepts from the book
- **Example**: 
  - Instead of: "How would you explain statistical significance?"
  - Get: "Why does the textbook distinguish between statistical and practical significance in drug trials?"

### 4. **Cost Reduction**
- **Before**: 2 LLM calls per topic (golden question + prerequisite check)
- **After**: 0-1 LLM calls per topic (only study question if enabled, and only if chunks available)
- **Savings**: ~50-100% reduction in LLM costs for question generation
- **Note**: Can skip question generation entirely with `--no-questions` flag for even faster plan generation

## Files Modified

### Models
- `app/models/plan.py` - Renamed `golden_question` → `study_question`
- `app/models/enriched_coverage.py` - Added `top_chunks` field to store excerpts

### Core Logic
- `app/tools/question_generator.py` - Complete rewrite:
  - Removed `generate_golden_question()`
  - Made `generate_prerequisite_check()` rule-based (no LLM)
  - Added `generate_study_question()` that uses RAG chunks
- `app/tools/rag_scout.py` - Store top 2-3 chunk excerpts in `EnrichedTopic`
- `app/tools/study_planner.py` - Updated to use new question generation

### CLI & Export
- `app/cli/generate_plan.py` - Updated help text and output display
- `app/tools/plan_export.py` - Updated markdown/CSV export to use `study_question`
- `docs/EXECUTION_PLAN.md` - Updated documentation

## Testing Recommendations

1. **Re-enrich existing coverages** to get `top_chunks` populated:
   ```bash
   python -m app.cli.enrich_coverage <exam_id>
   ```

2. **Generate a new plan** with questions enabled:
   ```bash
   python -m app.cli.generate_plan <exam_id> --start 2026-02-10
   ```

3. **Check the study questions** - They should now reference specific textbook concepts

## Migration Notes

- Old plans with `golden_question` or `prerequisite_check` fields will still load (fields are optional)
- New plans will only have `study_question` field
- Question quality should be significantly better (grounded in textbook)
- Plans are now cleaner without unnecessary prerequisite check noise

## Next Steps (Optional)

1. Consider making study questions even more specific by including page references
2. Add fallback questions for low-confidence topics (when RAG chunks are poor)
3. Batch LLM calls for better performance (currently sequential)
