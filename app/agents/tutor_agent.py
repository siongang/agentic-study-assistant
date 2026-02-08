"""Tutor agent: answers questions using RAG over ingested content."""
from google.adk.agents.llm_agent import Agent
from app.agents.tools import (
    search_textbook,
    list_available_exams
)

tutor_agent = Agent(
    model="gemini-3-flash-preview",
    name="tutor_agent",
    description="Answers study questions using semantic search over textbook content.",
    instruction="""Answer questions using semantic search over textbook content.

Process:
1. search_textbook(query, top_k=5, exam_file_id=None, textbook_file_id=None, chapter_number=None) - Find relevant passages
2. Generate grounded answer:
   - Base answer ONLY on retrieved chunks
   - Always cite page numbers (e.g., "pages 45-47")
   - Explain step-by-step with textbook examples
3. Suggest related concepts and practice problems

Critical: Never hallucinate. If no relevant content found, say so honestly.
If user specifies a textbook or chapter, pass textbook_file_id and/or chapter_number to search_textbook.
Use list_available_exams() to see available exam scopes for filtering.""",
    tools=[
        search_textbook,
        list_available_exams
    ]
)
