from typing import List, Optional
from sqlmodel import Session, select
from app.backend.models.incident_attachment import IncidentAttachment


class IncidentAttachmentRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, attachment: IncidentAttachment) -> IncidentAttachment:
        """Crear un nuevo adjunto"""
        self.session.add(attachment)
        self.session.commit()
        self.session.refresh(attachment)
        return attachment
    
    def get_by_id(self, attachment_id: int) -> Optional[IncidentAttachment]:
        """Obtener un adjunto por ID"""
        return self.session.get(IncidentAttachment, attachment_id)
    
    def get_by_incident_id(self, incident_id: int) -> List[IncidentAttachment]:
        """Obtener todos los adjuntos de un incidente"""
        statement = select(IncidentAttachment).where(
            IncidentAttachment.incident_id == incident_id
        ).order_by(IncidentAttachment.uploaded_at.desc())
        return list(self.session.exec(statement).all())
    
    def delete(self, attachment_id: int) -> bool:
        """Eliminar un adjunto"""
        attachment = self.get_by_id(attachment_id)
        if attachment:
            self.session.delete(attachment)
            self.session.commit()
            return True
        return False
    
    def delete_by_incident_id(self, incident_id: int) -> int:
        """Eliminar todos los adjuntos de un incidente (retorna cantidad eliminada)"""
        attachments = self.get_by_incident_id(incident_id)
        count = len(attachments)
        for attachment in attachments:
            self.session.delete(attachment)
        self.session.commit()
        return count
