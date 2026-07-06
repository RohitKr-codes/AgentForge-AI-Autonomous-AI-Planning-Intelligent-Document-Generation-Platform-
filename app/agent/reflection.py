"""
reflection.py
Optional bonus on top of the mandatory Tool Orchestration feature: a quick
self-check pass where the agent reviews its own generated sections and
flags anything that looks thin, off-topic, or incomplete before the final
document is handed back to the user.
"""

from app.agent.llm_client import llm_client


REFLECTION_PROMPT_TEMPLATE = """You are reviewing a document you just drafted, to check its quality.

Original user request:
\"\"\"{user_request}\"\"\"

Section titles generated: {section_titles}

In ONE short sentence (max 30 words), say whether the document plausibly
satisfies the request, or briefly note the one biggest gap if it doesn't.
Do not use markdown. Do not mention that you are an AI.
"""


def self_check(user_request: str, sections: dict) -> str:
    """Runs a lightweight reflection pass and returns a one-line verdict."""
    try:
        prompt = REFLECTION_PROMPT_TEMPLATE.format(
            user_request=user_request,
            section_titles=", ".join(sections.keys()),
        )
        return llm_client.generate_text(prompt)
    except Exception:  # noqa: BLE001
        # Reflection is a bonus — never let it break the main response.
        return "Reflection step skipped due to an internal error; document generated normally."
