"""Testing-related SQLAlchemy models."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class TestRun(Base):
    """Stores test execution results for a job."""

    __tablename__ = "test_runs"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    status = Column(String(50))
    results = Column(JSON)
    total_tests = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="test_runs")


class BugReport(Base):
    """Stores bug reports discovered during testing."""

    __tablename__ = "bug_reports"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    file_path = Column(String(512))
    error_type = Column(String(128))
    error_message = Column(Text)
    traceback_text = Column(Text)
    suggested_fix = Column(Text)
    severity = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="bug_reports")


class SecurityFinding(Base):
    """Stores security audit findings for a job."""

    __tablename__ = "security_findings"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    file_path = Column(String(512))
    line_number = Column(Integer, nullable=True)
    owasp_category = Column(String(128))
    severity = Column(String(50))
    description = Column(Text)
    code_snippet = Column(Text, nullable=True)
    suggested_fix = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="security_findings")
