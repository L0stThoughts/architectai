from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ArtifactBase(BaseModel):
    filename: str
    content_type: str

class ArtifactCreate(ArtifactBase):
    url: Optional[str]

class Artifact(ArtifactBase):
    id: int
    job_id: int
    url: Optional[str]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

class AgentMessageBase(BaseModel):
    role: str
    content: str

class AgentMessageCreate(AgentMessageBase):
    pass

class AgentMessage(AgentMessageBase):
    id: int
    job_id: int
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
