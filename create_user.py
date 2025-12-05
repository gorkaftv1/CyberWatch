import argparse
from passlib.context import CryptContext
from sqlmodel import Session

from app.backend.database import engine, init_db
from app.backend.models.user import User
from app.backend.core.constants import BCRYPT_MAX_PASSWORD_LENGTH

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(email: str, password: str, full_name: str, role: str = "analyst", is_active: bool = True):
    init_db()
    with Session(engine) as session:
        existing = session.query(User).filter(User.email == email).first()
        if existing:
            raise SystemExit(f"Ya existe un usuario con el email: {email}")

        # Truncar password a 72 bytes (limitación de bcrypt)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
            password = password_bytes[:BCRYPT_MAX_PASSWORD_LENGTH].decode('utf-8', errors='ignore')
        
        # Hashear la contraseña
        hashed_password = pwd_context.hash(password)

        user = User(
            email=email,
            password=hashed_password,
            full_name=full_name,
            role=role,
            is_active=is_active,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"Usuario creado: id={user.id}, email={user.email}, role={user.role}")


def main():
    parser = argparse.ArgumentParser(description="Crear usuario para CyberWatch.")
    parser.add_argument("--email", required=True, help="Email del usuario")
    parser.add_argument("--password", required=True, help="Contraseña (se hasheará automáticamente)")
    parser.add_argument("--full-name", required=True, help="Nombre completo")
    parser.add_argument("--role", default="analyst", choices=["admin", "analyst"], help="Rol del usuario")
    parser.add_argument("--inactive", action="store_true", help="Crear usuario inactivo")

    args = parser.parse_args()
    is_active = not args.inactive

    create_user(
        email=args.email,
        password=args.password,
        full_name=args.full_name,
        role=args.role,
        is_active=is_active,
    )


if __name__ == "__main__":
    main()
