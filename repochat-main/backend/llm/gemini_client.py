"""
Thin wrapper around the Gemini API for text generation.

Kept as its own module (rather than calling google-genai directly from the
RAG pipeline) so the model, provider, or prompting details can change later
without touching retrieval code.
"""

from google import genai
from google.genai import types

from backend.config import settings


class GeminiClient:
    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        api_key = api_key or settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name or settings.GEMINI_MODEL

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        """
        Sends a single prompt to Gemini and returns the plain-text response.
        temperature is kept low by default since this system prioritizes
        grounded, consistent answers over creative variation.
        """
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
            ),
        )
        return response.text or ""
