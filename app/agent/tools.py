"""
tools.py
Defines the tools available to the autonomous agent, plus a small registry
so the planner/executor can describe them to the LLM and dispatch calls
by name. This is the heart of the "Tool Orchestration" engineering feature:
the LLM decides WHICH tool to call and WITH WHAT arguments; this file is
responsible for actually executing that tool safely and returning real data.
"""

from datetime import datetime
import random


def get_current_datetime(_args: dict) -> dict:
    """Returns the current date and time — used for timestamps in documents."""
    now = datetime.now()
    return {
        "date": now.strftime("%d %B %Y"),
        "time": now.strftime("%I:%M %p"),
        "day": now.strftime("%A"),
    }


def get_mock_financial_data(args: dict) -> dict:
    """
    Returns realistic-looking (but mock) financial figures for a company or
    project, used when the agent needs numbers for a report/proposal.
    """
    seed_name = args.get("company_name", "the company")
    random.seed(len(seed_name))  # deterministic-ish per name, still varied
    return {
        "company_name": seed_name,
        "estimated_budget_usd": random.choice([15000, 25000, 42000, 60000, 85000]),
        "projected_roi_percent": random.choice([12, 18, 24, 30, 35]),
        "timeline_weeks": random.choice([4, 6, 8, 10, 12]),
        "risk_level": random.choice(["Low", "Medium", "Medium-High"]),
    }


def get_mock_market_trends(args: dict) -> dict:
    """Returns mock industry/market trend data for context in reports."""
    industry = args.get("industry", "technology")
    return {
        "industry": industry,
        "growth_rate_percent": random.choice([5, 8, 11, 14, 19]),
        "key_trend": random.choice([
            "increased automation adoption",
            "shift toward subscription-based pricing",
            "growing demand for AI-driven personalization",
            "rising emphasis on data privacy and compliance",
        ]),
        "competitive_pressure": random.choice(["Low", "Moderate", "High"]),
    }


def get_mock_team_data(args: dict) -> dict:
    """Returns a mock project team roster, used for project plans / SOPs."""
    project_name = args.get("project_name", "the project")
    return {
        "project_name": project_name,
        "team": [
            {"role": "Project Lead", "name": "A. Sharma"},
            {"role": "Engineer", "name": "R. Iyer"},
            {"role": "Designer", "name": "M. Fernandes"},
            {"role": "QA Analyst", "name": "S. Khan"},
        ],
    }


# --- Tool Registry -----------------------------------------------------
# Each entry describes the tool (so the LLM can be told what exists) and
# maps its name to the actual callable that executes it.

TOOL_REGISTRY = {
    "get_current_datetime": {
        "description": "Get the current date, time, and day of the week.",
        "args": {},
        "func": get_current_datetime,
    },
    "get_mock_financial_data": {
        "description": "Get mock budget, ROI, timeline and risk data for a company/project.",
        "args": {"company_name": "string"},
        "func": get_mock_financial_data,
    },
    "get_mock_market_trends": {
        "description": "Get mock industry growth rate and market trend data.",
        "args": {"industry": "string"},
        "func": get_mock_market_trends,
    },
    "get_mock_team_data": {
        "description": "Get a mock project team roster with roles and names.",
        "args": {"project_name": "string"},
        "func": get_mock_team_data,
    },
}


def describe_tools_for_prompt() -> str:
    """Renders the tool registry as text the LLM can read when planning."""
    lines = []
    for name, meta in TOOL_REGISTRY.items():
        args_desc = ", ".join(f"{k}: {v}" for k, v in meta["args"].items()) or "no arguments"
        lines.append(f"- {name}({args_desc}): {meta['description']}")
    return "\n".join(lines)


def call_tool(tool_name: str, args: dict) -> dict:
    """Safely dispatches a tool call by name. Returns an error dict if unknown."""
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        return {"error": f"Unknown tool '{tool_name}'"}
    try:
        return tool["func"](args or {})
    except Exception as e:  # noqa: BLE001
        return {"error": f"Tool '{tool_name}' failed: {e}"}
