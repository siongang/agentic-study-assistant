"""Generate study questions from textbook content (Phase 8+)."""
import os
from google import genai
from google.genai import types


def get_genai_client():
    """Get authenticated Google GenAI client."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment")
    
    client = genai.Client(api_key=api_key)
    return client


def generate_study_question(
    objective: str,
    chunk_excerpts: list[str],
    chapter_title: str = ""
) -> str:
    """
    Generate a study question based on actual textbook content.
    
    Args:
        objective: Learning objective text
        chunk_excerpts: List of relevant textbook excerpts (2-3)
        chapter_title: Optional chapter context
        
    Returns:
        A focused study question based on textbook content
    """
    # If no chunks available, return empty
    if not chunk_excerpts:
        return ""
    
    client = get_genai_client()
    
    # Build context from chunks (limit to top 2 for brevity)
    context_text = "\n\n".join(chunk_excerpts[:2])
    
    # Truncate if too long (max ~500 chars)
    if len(context_text) > 500:
        context_text = context_text[:500] + "..."
    
    chapter_context = f" in {chapter_title}" if chapter_title else ""
    
    prompt = f"""Learning objective{chapter_context}:
"{objective}"

Relevant textbook excerpt:
{context_text}

Based on the textbook content above, generate ONE focused study question that:
- Tests understanding of the specific concepts mentioned in the excerpt
- Requires applying or connecting ideas, not just recall
- Is answerable using the textbook content
- Starts with "Why", "How", or "What" and is under 25 words

Output only the question, no preamble."""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=100
            )
        )
        
        question = response.text.strip()
        
        # Remove quotes if LLM added them
        if question.startswith('"') and question.endswith('"'):
            question = question[1:-1]
        
        # Ensure it ends with a question mark
        if not question.endswith('?'):
            question += '?'
        
        return question
        
    except Exception as e:
        # If LLM fails, return empty (better than broken fallback)
        print(f"  ⚠️ Question generation failed: {e}")
        return ""
