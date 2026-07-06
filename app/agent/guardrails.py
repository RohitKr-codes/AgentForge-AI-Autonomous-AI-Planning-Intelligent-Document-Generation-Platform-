"""
guardrails.py
Lightweight request validation layer. Runs BEFORE any LLM call, so bad
input never wastes a Gemini call or reaches document generation.
"""

from app.config import settings


class GuardrailViolation(Exception):
    """Raised when a request fails validation."""
    pass


def validate_request(user_request: str) -> None:
    """
    Validates the incoming natural-language request.
    Raises GuardrailViolation with a human-readable reason on failure.
    """
    if not user_request or not user_request.strip():
        raise GuardrailViolation("Request cannot be empty.")

    text = user_request.strip()

    if len(text) < settings.MIN_REQUEST_LENGTH:
        raise GuardrailViolation(
            f"Request is too short (min {settings.MIN_REQUEST_LENGTH} characters)."
        )

    if len(text) > settings.MAX_REQUEST_LENGTH:
        raise GuardrailViolation(
            f"Request is too long (max {settings.MAX_REQUEST_LENGTH} characters)."
        )

    lowered = text.lower()
    for pattern in settings.BLOCKED_PATTERNS:
        if pattern in lowered:
            raise GuardrailViolation(
                "Request contains a disallowed instruction pattern and was rejected."
            )


def sanitize_for_document(text: str) -> str:
    """
    Basic sanitization before content is written into the Word document —
    strips control characters that could corrupt the .docx XML.
    """
    if not text:
        return ""
    return "".join(ch for ch in text if ch.isprintable() or ch in ("\n", "\t"))
