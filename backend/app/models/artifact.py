"""Artifact and AgentMessage SQLAlchemy models."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Artifact(Base):
    """Stores generated file artifacts for a job."""

    __tablename__ = "artifacts"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    file_path = Column(String(512))
    content = Column(Text)
    artifact_type = Column(String(128))
    language = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="artifacts")


class AgentMessage(Base):
    """Stores agent conversation messages for a job."""

    __tablename__ = "agent_messages"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    role = Column(String(64))
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
