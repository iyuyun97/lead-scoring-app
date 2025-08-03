# backend/models.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional

class LeadRequest(BaseModel):
    name: str
    email: Optional[EmailStr]
    company: Optional[str]
    position: Optional[str]
    industry: Optional[str]

class LeadScoreResponse(BaseModel):
    name: str
    score: float
    priority: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class User(BaseModel):
    username: str
    password: str