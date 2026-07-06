"""
models.py
SQLAlchemy ORM models for local persistence:
 - RequestLog: every incoming request the agent received
 - ExecutionLog: every step the agent executed, per request
 - AgentMemory: simple key-value conversational memory (used as an example
   of state the agent could recall across requests)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_request = Column(Text, nullable=False)
    document_type = Column(String(100), nullable=True)
    success = Column(String(10), default="pending")  # "true" / "false" / "pending"
    created_at = Column(DateTime, default=datetime.utcnow)

    steps = relationship("ExecutionLog", back_populates="request", cascade="all, delete-orphan")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("request_logs.id"))
    step_number = Column(Integer)
    title = Column(String(255))
    tool_used = Column(String(100), nullable=True)
    output_snippet = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    request = relationship("RequestLog", back_populates="steps")


class AgentMemory(Base):
    """
    Very lightweight conversational memory: stores the last N requests and
    their generated document types, so the agent can reference recent
    history when reasoning (e.g. 'the previous report was a proposal').
    """
    __tablename__ = "agent_memory"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
