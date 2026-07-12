"""Project and Job SQLAlchemy models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Project(Base):
    """Represents a user project with a product goal."""

    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    product_goal = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    jobs = relationship("Job", back_populates="project", lazy="selectin")


class Job(Base):
    """Represents a generation job within a project."""

    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    status = Column(String(50), default="PENDING")
    product_goal = Column(Text)
    input_data = Column(JSON)
    result = Column(JSON)
    current_phase = Column(String(50), default="PLAN")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="jobs")
    artifacts = relationship("Artifact", back_populates="job", lazy="selectin")
    test_runs = relationship("TestRun", back_populates="job", lazy="selectin")
    bug_reports = relationship("BugReport", back_populates="job", lazy="selectin")
    security_findings = relationship("SecurityFinding", back_populates="job", lazy="selectin")
