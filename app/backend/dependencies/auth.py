from fastapi import Depends, Request, HTTPException, status
from sqlmodel import Session, select

from app.backend.database import get_session
from app.backend.models import User


def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    email = request.cookies.get("user_email")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user