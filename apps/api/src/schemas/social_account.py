from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class SocialAccountBase(BaseModel):
    platform: str
    account_id: str

class SocialAccountCreate(SocialAccountBase):
    access_token: str

class SocialAccountUpdate(BaseModel):
    access_token: str

class SocialAccountResponse(SocialAccountBase):
    id: int
    owner_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
