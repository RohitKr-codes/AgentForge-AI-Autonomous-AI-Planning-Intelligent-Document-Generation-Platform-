"""
schemas.py
Pydantic models describing the shapes of data flowing through the API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    """Incoming request body for POST /agent"""
    request: str = Field(..., description="Natural language request from the user")


class TaskStep(BaseModel):
    """A single step in the agent's self-generated execution plan."""
    step_number: int
    title: str
    description: str
    tool_used: Optional[str] = None
    status: str = "pending"  # pending -> running -> done / failed


class ExecutionResult(BaseModel):
    """Result of executing a single plan step."""
    step_number: int
    title: str
    output: str
    tool_used: Optional[str] = None
    status: str


class AgentResponse(BaseModel):
    """Final response returned by POST /agent"""
    success: bool
    message: str
    document_type: Optional[str] = None
    task_list: List[TaskStep] = []
    execution_log: List[ExecutionResult] = []
    engineering_note: Optional[str] = None
    document_filename: Optional[str] = None
    download_url: Optional[str] = None
    reflection_note: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    details: Optional[Dict[str, Any]] = None
