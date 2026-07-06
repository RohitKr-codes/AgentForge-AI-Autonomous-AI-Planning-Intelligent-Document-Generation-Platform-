"""
executor.py
Walks through the plan produced by planner.py and actually executes each
step: calling tools where the plan calls for them, then asking the LLM to
draft the section content (incorporating any real tool data returned).

This is where "tool orchestration" and "error handling & recovery" both
live: if a tool fails or a section's content generation fails, the step is
marked failed but the agent continues with the remaining steps rather than
crashing the whole request.
"""

from app.agent.llm_client import llm_client
from app.agent.tools import call_tool
from app.agent.guardrails import sanitize_for_document
from app.schemas import ExecutionResult


SECTION_PROMPT_TEMPLATE = """You are drafting one section of a professional business
document titled "{document_title}" ({document_type}).

Original user request:
\"\"\"{user_request}\"\"\"

Section to write: {step_title}
Section purpose: {step_description}

{tool_data_block}

Write clear, professional, well-structured prose (or a bulleted list where more
appropriate) for this ONE section only. Do not repeat the section title in
your answer, do not add markdown headers, and do not mention that you are an AI.
Keep it focused and concrete — 100 to 220 words.
"""


def execute_plan(plan: dict, user_request: str) -> tuple:
    """
    Executes every step in the plan.
    Returns (execution_results: list[ExecutionResult], sections: dict[title -> content])
    """
    execution_results = []
    sections = {}

    document_title = plan.get("document_title", "Generated Document")
    document_type = plan.get("document_type", "business_report")

    for step in plan.get("steps", []):
        step_number = step.get("step_number", 0)
        title = step.get("title", "Untitled step")
        description = step.get("description", "")
        tool_name = step.get("tool_to_use")
        tool_args = step.get("tool_args") or {}

        tool_data_block = ""
        tool_used_label = None

        # --- Tool orchestration: call the tool the planner decided on ---
        if tool_name:
            try:
                tool_result = call_tool(tool_name, tool_args)
                if "error" in tool_result:
                    # Error handling & recovery: log the failure, continue
                    # without tool data rather than aborting the whole plan.
                    tool_data_block = (
                        f"(Note: attempted to use tool '{tool_name}' but it failed: "
                        f"{tool_result['error']}. Proceed using reasonable estimates instead.)"
                    )
                else:
                    tool_data_block = f"Supporting data from tool '{tool_name}': {tool_result}"
                    tool_used_label = tool_name
            except Exception as e:  # noqa: BLE001
                tool_data_block = (
                    f"(Note: tool '{tool_name}' raised an unexpected error ({e}). "
                    "Proceed using reasonable estimates instead.)"
                )

        # --- Content generation for this section ---
        try:
            prompt = SECTION_PROMPT_TEMPLATE.format(
                document_title=document_title,
                document_type=document_type,
                user_request=user_request,
                step_title=title,
                step_description=description,
                tool_data_block=tool_data_block,
            )
            content = llm_client.generate_text(prompt)
            content = sanitize_for_document(content)
            status = "done"
        except Exception as e:  # noqa: BLE001
            # Fallback content so the document generation never breaks
            content = (
                f"[This section could not be generated automatically due to an error: {e}. "
                f"Placeholder: {description}]"
            )
            status = "failed"

        sections[title] = content
        execution_results.append(
            ExecutionResult(
                step_number=step_number,
                title=title,
                output=content[:180] + ("..." if len(content) > 180 else ""),
                tool_used=tool_used_label,
                status=status,
            )
        )

    return execution_results, sections
