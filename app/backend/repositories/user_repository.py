from typing import Optional
from sqlmodel import Session, select

from app.backend.models.user import User


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()
