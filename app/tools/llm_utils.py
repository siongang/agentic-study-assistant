"""Shared LLM utilities."""
import os
from typing import Optional

from google import genai
from google.genai import types


def call_gemini(
    prompt: str,
    model: str = "gemini-2.0-flash-exp",
    temperature: float = 0.7,
    max_output_tokens: int = 8192
) -> str:
    """
    Call Gemini API with a text prompt.
    
    Args:
        prompt: The text prompt
        model: Model name
        temperature: Sampling temperature (0.0-1.0)
        max_output_tokens: Maximum tokens in response
        
    Returns:
        Response text
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )
    )
    
    return response.text
