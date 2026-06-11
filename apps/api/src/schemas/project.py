from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class ProjectKeywordBase(BaseModel):
    keyword: str

class ProjectKeywordCreate(ProjectKeywordBase):
    pass

class ProjectKeywordResponse(ProjectKeywordBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ProjectBase(BaseModel):
    name: str
    industry: Optional[str] = None

class ProjectCreate(ProjectBase):
    keywords: List[str] = []

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    keywords: List[ProjectKeywordResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
