from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.backend.dependencies.auth import get_current_user
from app.backend.repositories.user_repository import UserRepository
from app.backend.database import get_session
from sqlmodel import Session
from app.backend.models.user import User
from passlib.context import CryptContext
from app.backend.core.constants import BCRYPT_MAX_PASSWORD_LENGTH

router = APIRouter(prefix="/users", tags=["users"])
templates = Jinja2Templates(directory="app/frontend/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def require_admin(user: User = Depends(get_current_user)):
    """Dependencia que requiere que el usuario sea administrador"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado: solo administradores")
    return user

@router.get("")
async def list_users(
    request: Request,
    user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """Lista todos los usuarios (solo admin)"""
    user_repo = UserRepository(session)
    users = user_repo.get_all()
    
    return templates.TemplateResponse("users.html", {
        "request": request,
        "user": user,
        "users": users
    })

@router.get("/new")
async def new_user_form(
    request: Request,
    user: User = Depends(require_admin)
):
    """Formulario para crear nuevo usuario"""
    return templates.TemplateResponse("user_form.html", {
        "request": request,
        "user": user,
        "edit_user": None,
        "mode": "create"
    })

@router.post("/create")
async def create_user(
    request: Request,
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    is_active: str = Form(...),
    user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """Crea un nuevo usuario"""
    user_repo = UserRepository(session)
    
    # Verificar si el email ya existe
    existing_user = user_repo.get_by_email(email)
    if existing_user:
        return templates.TemplateResponse("user_form.html", {
            "request": request,
            "user": user,
            "edit_user": None,
            "mode": "create",
            "error": "El email ya está registrado"
        })
    
    # Truncar password a 72 bytes (limitación de bcrypt)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
        password = password_bytes[:BCRYPT_MAX_PASSWORD_LENGTH].decode('utf-8', errors='ignore')
    
    # Hashear password
    hashed_password = pwd_context.hash(password)
    
    # Crear usuario
    new_user = User(
        email=email,
        full_name=full_name,
        password=hashed_password,
        role=role,
        is_active=(is_active.lower() == "true")
    )
    
    user_repo.create(new_user)
    return RedirectResponse(url="/users", status_code=303)

@router.get("/{user_id}/edit")
async def edit_user_form(
    request: Request,
    user_id: int,
    user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """Formulario para editar usuario"""
    user_repo = UserRepository(session)
    edit_user = user_repo.get_by_id(user_id)
    
    if not edit_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return templates.TemplateResponse("user_form.html", {
        "request": request,
        "user": user,
        "edit_user": edit_user,
        "mode": "edit"
    })

@router.post("/{user_id}/update")
async def update_user(
    request: Request,
    user_id: int,
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(None),
    role: str = Form(...),
    is_active: str = Form(...),
    user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """Actualiza un usuario existente"""
    user_repo = UserRepository(session)
    edit_user = user_repo.get_by_id(user_id)
    
    if not edit_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizar datos
    edit_user.email = email
    edit_user.full_name = full_name
    edit_user.role = role
    edit_user.is_active = (is_active.lower() == "true")
    
    # Solo actualizar password si se proporciona uno nuevo
    if password and password.strip():
        # Truncar password a 72 bytes (limitación de bcrypt)
        password_bytes = new_password.encode('utf-8')
        if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
            new_password = password_bytes[:BCRYPT_MAX_PASSWORD_LENGTH].decode('utf-8', errors='ignore')
        edit_user.password = pwd_context.hash(password)
    
    user_repo.update(edit_user)
    return RedirectResponse(url="/users", status_code=303)

@router.post("/{user_id}/delete")
async def delete_user(
    user_id: int,
    user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """Elimina un usuario"""
    user_repo = UserRepository(session)
    
    # No permitir que un admin se elimine a sí mismo
    if user.id == user_id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
    
    success = user_repo.delete(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return RedirectResponse(url="/users", status_code=303)
