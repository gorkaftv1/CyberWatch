from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.backend.database import get_session
from app.backend.models import User

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/frontend/templates")


def authenticate_user(session: Session, email: str, password: str):
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()

    print(f"Authenticating user: email={email}, password={password}")
    print(f"Found user: {user}")
    if not user:
        return None
    if user.password != password:
        return None
    if not user.is_active:
        return None
    return user


@router.get("/login", response_class=HTMLResponse)
async def login_get(
    request: Request,
    session: Session = Depends(get_session),
):
    email = request.cookies.get("user_email")
    if email:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        if user and user.is_active:
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
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
