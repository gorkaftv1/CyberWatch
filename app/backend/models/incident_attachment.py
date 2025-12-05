from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class IncidentAttachment(SQLModel, table=True):
    """Modelo para almacenar archivos de texto adjuntos a incidentes"""
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id", index=True)
    filename: str = Field(max_length=255)
    content: str = Field(max_length=1_000_000)  # Máximo 1MB de texto
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
