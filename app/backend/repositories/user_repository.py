from typing import Optional, List
from sqlmodel import Session, select

from app.backend.models.user import User


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_all_users(session: Session) -> List[User]:
    """Obtiene todos los usuarios del sistema"""
    statement = select(User).order_by(User.full_name)
    return list(session.exec(statement).all())


class UserRepository:
    """Repositorio para operaciones CRUD de usuarios"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_all(self) -> List[User]:
        """Obtiene todos los usuarios"""
        statement = select(User).order_by(User.full_name)
        return list(self.session.exec(statement).all())
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por ID"""
        return self.session.get(User, user_id)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por email"""
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()
    
    def create(self, user: User) -> User:
        """Crea un nuevo usuario"""
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def update(self, user: User) -> User:
        """Actualiza un usuario existente"""
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """Elimina un usuario por ID"""
        user = self.get_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False
    
    def get_active_analysts(self) -> List[User]:
        """Obtiene todos los analistas activos del sistema"""
        statement = select(User).where(User.is_active == True).order_by(User.full_name)
        return list(self.session.exec(statement).all())
    
    def get_active_users(self) -> List[User]:
        """Obtiene todos los usuarios activos del sistema"""
        statement = select(User).where(User.is_active == True).order_by(User.full_name)
        return list(self.session.exec(statement).all())
