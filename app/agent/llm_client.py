"""
llm_client.py
Thin wrapper around Google Gemini (free tier). Centralizing all LLM calls
here means the rest of the codebase never touches the SDK directly —
if the model or provider changes later, only this file changes.
"""

import json
import time
from google import genai
from app.config import settings


class LLMClient:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file before starting the server."
            )
        # Uses the current `google-genai` SDK (the older `google-generativeai`
        # package is deprecated and no longer receives updates).
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

    def generate_text(self, prompt: str, retries: int = 2) -> str:
        """
        Sends a plain text prompt to Gemini and returns the text response.
        Includes simple retry logic since free-tier endpoints occasionally
        rate-limit or hiccup.
        """
        last_error = None
        for attempt in range(retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text.strip()
                raise ValueError("Empty response from Gemini")
            except Exception as e:  # noqa: BLE001
                last_error = e
                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))  # simple backoff
                    continue
        raise RuntimeError(f"Gemini call failed after {retries + 1} attempts: {last_error}")

    def generate_json(self, prompt: str, retries: int = 2) -> dict:
        """
        Asks Gemini for a strict JSON response and parses it. If parsing
        fails, retries with a stricter follow-up instruction. This is the
        backbone of the planner (task list generation).
        """
        json_prompt = (
            prompt
            + "\n\nRespond with ONLY valid JSON. No markdown fences, no commentary, "
            "no explanation text before or after the JSON."
        )
        last_error = None
        for attempt in range(retries + 1):
            try:
                raw = self.generate_text(json_prompt, retries=1)
                cleaned = self._strip_json_fences(raw)
                return json.loads(cleaned)
            except Exception as e:  # noqa: BLE001
                last_error = e
                if attempt < retries:
                    json_prompt = (
                        prompt
                        + "\n\nIMPORTANT: Your previous response was not valid JSON. "
                        "Respond with ONLY a valid JSON object/array. No backticks, no prose."
                    )
                    continue
        raise RuntimeError(f"Gemini JSON generation failed after retries: {last_error}")

    @staticmethod
    def _strip_json_fences(text: str) -> str:
        """Removes ```json ... ``` fences if the model adds them anyway."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()
        return text


llm_client = LLMClient()
