from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TestRunBase(BaseModel):
    results: Optional[str]

class TestRunCreate(TestRunBase):
    pass

class TestRun(TestRunBase):
    id: int
    job_id: int
    status: Optional[str]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

class BugReportBase(BaseModel):
    description: str
    severity: str

class BugReport(BugReportBase):
    id: int
    test_run_id: int
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

class SecurityFindingBase(BaseModel):
    rule: str
    details: str
    severity: str

class SecurityFinding(SecurityFindingBase):
    id: int
    test_run_id: int
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
