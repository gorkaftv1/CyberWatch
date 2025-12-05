from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Session, select, col

from app.backend.models.incident import Incident


class IncidentRepository:
    """Repositorio para operaciones CRUD de incidentes"""

    def __init__(self, session: Session):
        self.session = session

    def get_all(
        self,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        owner: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> list[Incident]:
        """Obtener todos los incidentes con filtros opcionales"""
        statement = select(Incident)

        if severity:
            statement = statement.where(Incident.severity == severity)
        if status:
            statement = statement.where(Incident.status == status)
        if source:
            statement = statement.where(Incident.source == source)
        if owner:
            statement = statement.where(Incident.owner == owner)

        statement = statement.order_by(Incident.detected_at.desc())

        if limit:
            statement = statement.limit(limit)
        if offset:
            statement = statement.offset(offset)

        return list(self.session.exec(statement).all())

    def get_by_id(self, incident_id: int) -> Optional[Incident]:
        """Obtener un incidente por ID"""
        return self.session.get(Incident, incident_id)

    def get_by_code(self, code: str) -> Optional[Incident]:
        """Obtener un incidente por código"""
        statement = select(Incident).where(Incident.code == code)
        return self.session.exec(statement).first()

    def create(self, incident_data: dict) -> Incident:
        """Crear un nuevo incidente"""
        incident = Incident(**incident_data)
        self.session.add(incident)
        self.session.commit()
        self.session.refresh(incident)
        return incident

    def update(self, incident_id: int, incident_data: dict) -> Optional[Incident]:
        """Actualizar un incidente existente"""
        incident = self.get_by_id(incident_id)
        if not incident:
            return None

        # Actualizar campos
        for key, value in incident_data.items():
            if hasattr(incident, key):
                setattr(incident, key, value)

        # Actualizar timestamp
        incident.updated_at = datetime.now(timezone.utc)

        self.session.add(incident)
        self.session.commit()
        self.session.refresh(incident)
        return incident

    def delete(self, incident_id: int) -> bool:
        """Eliminar un incidente"""
        incident = self.get_by_id(incident_id)
        if not incident:
            return False

        self.session.delete(incident)
        self.session.commit()
        return True

    def count(
        self,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> int:
        """Contar incidentes con filtros opcionales"""
        statement = select(Incident)

        if severity:
            statement = statement.where(Incident.severity == severity)
        if status:
            statement = statement.where(Incident.status == status)
        if source:
            statement = statement.where(Incident.source == source)
        if owner:
            statement = statement.where(Incident.owner == owner)

        return len(list(self.session.exec(statement).all()))

    def get_unique_values(self, field: str) -> list[str]:
        """Obtener valores únicos de un campo (para filtros)"""
        if field == "severity":
            statement = select(Incident.severity).distinct()
        elif field == "status":
            statement = select(Incident.status).distinct()
        elif field == "source":
            statement = select(Incident.source).distinct()
        elif field == "owner":
            statement = select(Incident.owner).distinct()
        else:
            return []

        results = self.session.exec(statement).all()
        return [r for r in results if r is not None]

    def search(self, query: str) -> list[Incident]:
        """Buscar incidentes por texto en título, descripción o código"""
        statement = select(Incident).where(
            col(Incident.title).contains(query)
            | col(Incident.description).contains(query)
            | col(Incident.code).contains(query)
        )
        return list(self.session.exec(statement).all())


def get_incident_repository(session: Session) -> IncidentRepository:
    """Dependency injection helper"""
    return IncidentRepository(session)
