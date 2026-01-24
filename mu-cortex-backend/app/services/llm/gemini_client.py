"""
Gemini LLM client for answer generation.

This module provides a reusable async interface to Google's Gemini 2.5 Flash model
for generating text responses in the MU-Cortex backend.
"""
import os
from typing import Optional

from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from backend .env file
# Path: mu-cortex-backend/.env
env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
load_dotenv(env_path)

# Also check root .env (where GEMINI_API_KEY might be stored)
root_env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env")
load_dotenv(root_env_path, override=False)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "Missing environment variable: GEMINI_API_KEY. "
        "Please set it in .env file (root or mu-cortex-backend/.env)"
    )

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model: Gemini 2.5 Flash
MODEL_NAME = "gemini-2.5-flash"
_model: Optional[genai.GenerativeModel] = None


def _get_model() -> genai.GenerativeModel:
    """Get or create the Gemini model instance."""
    global _model
    if _model is None:
        _model = genai.GenerativeModel(MODEL_NAME)
    return _model


async def generate_text(prompt: str) -> str:
    """
    Generate text using Gemini 2.5 Flash model.

    Args:
        prompt: The complete prompt string to send to the model.

    Returns:
        The generated text response as a string, with leading/trailing whitespace stripped.

    Raises:
        RuntimeError: If the API key is missing or if the API call fails.
        Exception: For other API-related errors (network, rate limits, etc.).
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    try:
        model = _get_model()
        
        # Generate content (async-friendly, but genai uses sync calls)
        # We'll run it in a thread pool for true async behavior
        import asyncio
        
        def _generate_sync():
            response = model.generate_content(prompt)
            return response.text
        
        # Run the sync call in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, _generate_sync)
        
        # Strip whitespace and return
        return text.strip() if text else ""
        
    except Exception as e:
        # Re-raise with a cleaner error message
        error_msg = str(e)
        if "API_KEY" in error_msg or "api key" in error_msg.lower():
            raise RuntimeError(
                "Gemini API key is invalid or missing. "
                "Please check your GEMINI_API_KEY environment variable."
            ) from e
        raise RuntimeError(f"Failed to generate text with Gemini: {error_msg}") from e
