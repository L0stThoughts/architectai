"""Pydantic schemas for projects, jobs, and API payloads."""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str
    description: Optional[str] = None
    product_goal: str


class ProjectRead(BaseModel):
    """Schema for reading a project."""

    id: int
    name: str
    description: Optional[str] = None
    product_goal: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    jobs: List["JobRead"] = []

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    """Schema for creating a job."""

    product_goal: Optional[str] = None


class JobRead(BaseModel):
    """Schema for reading a job."""

    id: int
    project_id: int
    status: str
    product_goal: Optional[str] = None
    current_phase: Optional[str] = None
    result: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ArtifactRead(BaseModel):
    """Schema for reading an artifact."""

    id: int
    job_id: int
    file_path: str
    content: Optional[str] = None
    artifact_type: Optional[str] = None
    language: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestRunRead(BaseModel):
    """Schema for reading test run results."""

    id: int
    job_id: int
    status: Optional[str] = None
    results: Optional[Any] = None
    total_tests: Optional[int] = None
    passed: Optional[int] = None
    failed: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BugReportRead(BaseModel):
    """Schema for reading a bug report."""

    id: int
    job_id: int
    file_path: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    suggested_fix: Optional[str] = None
    severity: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SecurityFindingRead(BaseModel):
    """Schema for reading a security finding."""

    id: int
    job_id: int
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    owasp_category: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    code_snippet: Optional[str] = None
    suggested_fix: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


ProjectRead.model_rebuild()
