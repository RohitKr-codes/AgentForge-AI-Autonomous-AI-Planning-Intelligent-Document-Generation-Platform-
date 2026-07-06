"""
planner.py
This is where "autonomous planning" happens: given a raw natural-language
request, the agent (via Gemini) decides for itself:
  1. what kind of business document is being asked for
  2. what sections/steps are needed to build it
  3. which tool (if any) each step should use to get supporting data

The output is a structured JSON plan that executor.py then works through
step by step. If the request is ambiguous or missing details, the agent
is explicitly instructed to make and state reasonable assumptions rather
than fail — this is what the "complex test case" exercises.
"""

from app.agent.llm_client import llm_client
from app.agent.tools import describe_tools_for_prompt
from app.schemas import TaskStep


PLANNER_PROMPT_TEMPLATE = """You are the planning module of an autonomous AI agent.
Your job is to read a user's natural-language request and design a step-by-step
execution plan to fulfil it by producing a business document.

USER REQUEST:
\"\"\"{user_request}\"\"\"

AVAILABLE TOOLS (call these where they would add real, useful data):
{tools_description}

INSTRUCTIONS:
- Decide what type of business document best satisfies the request
  (choose from: proposal, meeting_minutes, project_plan, business_report,
  technical_design, sop, product_specification — or a close variant).
- If the request is ambiguous, vague, or missing information, DO NOT ask a
  clarifying question. Instead, make the most reasonable assumption, and
  state that assumption clearly in the plan's "assumptions" field.
- Break the work into 4 to 6 concrete steps. Typical steps include:
  gathering supporting data (via a tool), drafting each major section, and
  a final review/formatting step.
- For any step that would benefit from real supporting data, set "tool_to_use"
  to the exact tool name from the list above and provide "tool_args" as an
  object matching that tool's arguments. Otherwise set both to null.

Respond with ONLY a JSON object of this exact shape:
{{
  "document_type": "string",
  "document_title": "string",
  "assumptions": ["string", ...],
  "steps": [
    {{
      "step_number": 1,
      "title": "string",
      "description": "string",
      "tool_to_use": "string or null",
      "tool_args": {{"key": "value"}} or null
    }}
  ]
}}
"""


def create_plan(user_request: str) -> dict:
    """
    Calls the LLM to autonomously generate a document type + step plan.
    Returns a dict with keys: document_type, document_title, assumptions, steps.
    """
    prompt = PLANNER_PROMPT_TEMPLATE.format(
        user_request=user_request,
        tools_description=describe_tools_for_prompt(),
    )
    plan = llm_client.generate_json(prompt)

    # Defensive defaults in case the model omits a field
    plan.setdefault("document_type", "business_report")
    plan.setdefault("document_title", "Generated Document")
    plan.setdefault("assumptions", [])
    plan.setdefault("steps", [])

    return plan


def plan_to_task_steps(plan: dict) -> list:
    """Converts the raw plan dict into validated TaskStep pydantic models."""
    task_steps = []
    for s in plan.get("steps", []):
        task_steps.append(
            TaskStep(
                step_number=s.get("step_number", len(task_steps) + 1),
                title=s.get("title", "Untitled step"),
                description=s.get("description", ""),
                tool_used=s.get("tool_to_use"),
                status="pending",
            )
        )
    return task_steps
