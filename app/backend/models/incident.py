from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Incident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    title: str
    severity: str = Field(index=True)
    status: str = Field(index=True)
    source: str
    owner: Optional[str] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None
