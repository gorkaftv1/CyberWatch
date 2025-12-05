from datetime import datetime, timezone
from typing import Optional
import csv
import io

from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File
from fastapi import status as http_status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.backend.database import get_session
from app.backend.models import Incident, User
from app.backend.models.incident_attachment import IncidentAttachment
from app.backend.repositories.incident_repository import get_incident_repository, IncidentRepository
from app.backend.repositories.user_repository import UserRepository
from app.backend.repositories.incident_attachment_repository import IncidentAttachmentRepository
from app.backend.dependencies.auth import get_current_user
from app.backend.core.constants import PAGINATION_OPTIONS, DEFAULT_PER_PAGE

router = APIRouter(prefix="/incidents", tags=["incidents"])
templates = Jinja2Templates(directory="app/frontend/templates")


@router.get("", response_class=HTMLResponse)
async def list_incidents(
    request: Request,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    owner: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 25,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Listar todos los incidentes con filtros opcionales"""
    repo = get_incident_repository(session)
    
    # Validar per_page
    if per_page not in PAGINATION_OPTIONS:
        per_page = DEFAULT_PER_PAGE
    
    # Calcular offset
    offset = (page - 1) * per_page
    
    # Si es analista y no hay filtro de owner, establecer por defecto al analista actual
    if user.role == 'analyst' and owner is None:
        owner = user.full_name
    
    if search:
        incidents = repo.search(search)
        # Filtrar por owner si está establecido
        if owner:
            incidents = [inc for inc in incidents if inc.owner == owner]
        total_incidents = len(incidents)
        incidents = incidents[offset:offset + per_page]
    else:
        # Contar total de incidentes con filtros
        total_incidents = repo.count(
            severity=severity,
            status=status,
            source=source,
            owner=owner,
        )
        
        incidents = repo.get_all(
            severity=severity,
            status=status,
            source=source,
            owner=owner,
            limit=per_page,
            offset=offset,
        )
    
    # Calcular número total de páginas
    total_pages = (total_incidents + per_page - 1) // per_page
    
    # Obtener valores únicos para los filtros
    severities = repo.get_unique_values("severity")
    statuses = repo.get_unique_values("status")
    sources = repo.get_unique_values("source")
    owners = repo.get_unique_values("owner")
    
    return templates.TemplateResponse(
        "incidents.html",
        {
            "request": request,
            "user": user,
            "incidents": incidents,
            "severities": severities,
            "statuses": statuses,
            "sources": sources,
            "owners": owners,
            "now": datetime.now(timezone.utc),
            "page": page,
            "per_page": per_page,
            "total_incidents": total_incidents,
            "total_pages": total_pages,
            "filters": {
                "severity": severity,
                "status": status,
                "source": source,
                "owner": owner,
                "search": search,
            }
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_incident_form(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Mostrar formulario de creación de incidente"""
    repo = get_incident_repository(session)
    user_repo = UserRepository(session)
    
    # Obtener valores para los selectores
    sources = repo.get_unique_values("source")
    analysts = user_repo.get_active_analysts()
    
    return templates.TemplateResponse(
        "incident_form.html",
        {
            "request": request,
            "user": user,
            "incident": None,
            "sources": sources,
            "analysts": analysts,
            "mode": "create",
        },
    )


@router.post("/new")
async def create_incident(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    severity: str = Form(...),
    status: str = Form(...),
    source: str = Form(...),
    owner: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Crear un nuevo incidente"""
    repo = get_incident_repository(session)
    
    # Verificar que el código no exista
    existing = repo.get_by_code(code)
    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un incidente con el código {code}"
        )
    
    incident_data = {
        "code": code,
        "title": title,
        "severity": severity,
        "status": status,
        "source": source,
        "owner": owner if owner else None,
        "description": description if description else None,
        "detected_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    
    repo.create(incident_data)
    return RedirectResponse(url="/incidents", status_code=http_status.HTTP_303_SEE_OTHER)


@router.get("/{incident_id}", response_class=HTMLResponse)
async def view_incident(
    request: Request,
    incident_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Ver detalle de un incidente"""
    repo = get_incident_repository(session)
    incident = repo.get_by_id(incident_id)
    
    if not incident:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )
    
    # Obtener logs adjuntos
    attachment_repo = IncidentAttachmentRepository(session)
    attachments = attachment_repo.get_by_incident_id(incident_id)
    
    return templates.TemplateResponse(
        "incident_detail.html",
        {
            "request": request,
            "user": user,
            "incident": incident,
            "attachments": attachments,
        },
    )


@router.get("/{incident_id}/edit", response_class=HTMLResponse)
async def edit_incident_form(
    request: Request,
    incident_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Mostrar formulario de edición de incidente"""
    repo = get_incident_repository(session)
    user_repo = UserRepository(session)
    attachment_repo = IncidentAttachmentRepository(session)
    incident = repo.get_by_id(incident_id)
    
    if not incident:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )
    
    # Obtener valores para los selectores
    sources = repo.get_unique_values("source")
    analysts = user_repo.get_active_analysts()
    attachments = attachment_repo.get_by_incident_id(incident_id)
    
    return templates.TemplateResponse(
        "incident_form.html",
        {
            "request": request,
            "user": user,
            "incident": incident,
            "sources": sources,
            "analysts": analysts,
            "attachments": attachments,
            "mode": "edit",
        },
    )


@router.post("/{incident_id}/edit")
async def update_incident(
    request: Request,
    incident_id: int,
    title: str = Form(...),
    severity: str = Form(...),
    status: str = Form(...),
    source: str = Form(...),
    owner: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Actualizar un incidente existente"""
    repo = get_incident_repository(session)
    
    incident_data = {
        "title": title,
        "severity": severity,
        "status": status,
        "source": source,
        "owner": owner if owner else None,
        "description": description if description else None,
    }
    
    updated_incident = repo.update(incident_id, incident_data)
    
    if not updated_incident:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )
    
    return RedirectResponse(
        url=f"/incidents/{incident_id}",
        status_code=http_status.HTTP_303_SEE_OTHER
    )


@router.post("/{incident_id}/delete")
async def delete_incident(
    incident_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Eliminar un incidente"""
    repo = get_incident_repository(session)
    
    success = repo.delete(incident_id)
    
    if not success:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )
    
    return RedirectResponse(url="/incidents", status_code=http_status.HTTP_303_SEE_OTHER)


@router.get("/export/csv")
async def export_incidents_csv(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    owner: Optional[str] = None,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Exportar incidentes a CSV"""
    repo = get_incident_repository(session)
    
    incidents = repo.get_all(
        severity=severity,
        status=status,
        source=source,
        owner=owner,
    )
    
    # Crear CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escribir encabezados
    writer.writerow([
        "ID",
        "Código",
        "Título",
        "Severidad",
        "Estado",
        "Origen",
        "Responsable",
        "Fecha detección",
        "Última actualización",
        "Descripción",
    ])
    
    # Escribir datos
    for inc in incidents:
        writer.writerow([
            inc.id,
            inc.code,
            inc.title,
            inc.severity,
            inc.status,
            inc.source,
            inc.owner or "",
            inc.detected_at.strftime("%Y-%m-%d %H:%M:%S") if inc.detected_at else "",
            inc.updated_at.strftime("%Y-%m-%d %H:%M:%S") if inc.updated_at else "",
            inc.description or "",
        ])
    
    # Preparar respuesta
    output.seek(0)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"cyberwatch_incidents_{timestamp}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/{incident_id}/assign")
async def assign_incident(
    incident_id: int,
    owner: str = Form(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Asignar o cambiar el responsable de un incidente"""
    repo = get_incident_repository(session)
    incident = repo.get_by_id(incident_id)
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    
    incident.owner = owner
    incident.updated_at = datetime.now(timezone.utc)
    repo.update(incident)
    
    return RedirectResponse(url="/incidents", status_code=303)


@router.post("/{incident_id}/upload-attachment")
async def upload_attachment(
    incident_id: int,
    attachment: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Subir un archivo de texto adjunto a un incidente"""
    repo = get_incident_repository(session)
    attachment_repo = IncidentAttachmentRepository(session)
    
    # Verificar que el incidente existe
    incident = repo.get_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    
    # Verificar que es un archivo .txt
    if not attachment.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .txt")
    
    # Leer el contenido del archivo
    try:
        content = await attachment.read()
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="El archivo no es un archivo de texto válido")
    
    # Crear el attachment
    new_attachment = IncidentAttachment(
        incident_id=incident_id,
        filename=attachment.filename,
        content=text_content
    )
    attachment_repo.create(new_attachment)
    
    return RedirectResponse(url=f"/incidents/{incident_id}/edit", status_code=303)


@router.post("/{incident_id}/attachments/{attachment_id}/delete")
async def delete_attachment(
    incident_id: int,
    attachment_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Eliminar un archivo adjunto"""
    attachment_repo = IncidentAttachmentRepository(session)
    
    # Verificar que el attachment existe y pertenece al incidente
    attachment = attachment_repo.get_by_id(attachment_id)
    if not attachment or attachment.incident_id != incident_id:
        return RedirectResponse(
            url=f"/incidents/{incident_id}?error=Log+no+encontrado",
            status_code=303
        )
    
    filename = attachment.filename
    attachment_repo.delete(attachment_id)
    
    # Actualizar timestamp del incidente
    repo = get_incident_repository(session)
    incident = repo.get_by_id(incident_id)
    if incident:
        incident.updated_at = datetime.now(timezone.utc)
        session.add(incident)
        session.commit()
    
    return RedirectResponse(
        url=f"/incidents/{incident_id}?success=Log+'{filename}'+eliminado+correctamente",
        status_code=303
    )
    
    return RedirectResponse(url="/incidents", status_code=303)
