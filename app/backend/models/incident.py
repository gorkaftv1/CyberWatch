from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Incident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True, max_length=50)
    title: str = Field(max_length=200)
    severity: str = Field(index=True, max_length=20)
    status: str = Field(index=True, max_length=50)
    source: str = Field(max_length=50)
    owner: Optional[str] = Field(default=None, max_length=200)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = Field(default=None, max_length=5000)
