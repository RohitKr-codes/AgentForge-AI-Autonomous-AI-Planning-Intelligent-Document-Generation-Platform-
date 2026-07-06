"""
config.py
Loads environment variables and holds application-wide settings.
"""

import os
from dotenv import load_dotenv

# Load variables from .env into the environment
load_dotenv()


class Settings:
    """Centralized application settings."""

    # --- Gemini LLM ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # --- App ---
    APP_NAME: str = "Autonomous Agent - Document Builder"
    APP_VERSION: str = "1.0.0"

    # --- Storage ---
    OUTPUT_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    DB_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db")

    # --- Guardrails ---
    MIN_REQUEST_LENGTH: int = 5
    MAX_REQUEST_LENGTH: int = 4000

    # Simple denylist of suspicious patterns (prompt injection / abuse attempts)
    BLOCKED_PATTERNS = [
        "ignore previous instructions",
        "ignore all previous instructions",
        "disregard your instructions",
        "system prompt",
        "reveal your prompt",
    ]


settings = Settings()

# Ensure required directories exist at import time
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
