from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from passlib.context import CryptContext

from app.backend.database import get_session
from app.backend.models import User

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/frontend/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def authenticate_user(session: Session, email: str, password: str):
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()

    if not user:
        return None
    
    # Intentar verificar con bcrypt
    try:
        if not pwd_context.verify(password, user.password):
            return None
    except Exception:
        # Si falla, puede ser texto plano (migración pendiente)
        # Verificar texto plano y migrar automáticamente
        if user.password != password:
            return None
        
        # Migrar la contraseña a bcrypt
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode('utf-8', errors='ignore')
        
        user.password = pwd_context.hash(password)
        session.add(user)
        session.commit()
    
    if not user.is_active:
        return None
    return user


@router.get("/login", response_class=HTMLResponse)
async def login_get(
    request: Request,
    error: str = None,
    session: Session = Depends(get_session),
):
    email = request.cookies.get("user_email")
    if email:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        if user and user.is_active:
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    # Mensajes de error personalizados
    error_messages = {
        "session_expired": "Tu sesión ha expirado. Por favor, inicia sesión nuevamente.",
        "no_session": "Debes iniciar sesión para acceder a esta página.",
        "invalid_session": "Tu sesión es inválida. Por favor, inicia sesión nuevamente."
    }
    error_message = error_messages.get(error, None)
    
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error_message},
    )


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = authenticate_user(session, email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Credenciales inválidas"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie("user_email", user.email)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("user_email")
    return response
