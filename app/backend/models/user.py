from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    password: str = Field(max_length=255)
    full_name: str = Field(max_length=200)
    is_active: bool = Field(default=True)
    role: str = Field(default="analyst", max_length=20)
