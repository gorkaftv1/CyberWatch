"""
Script para migrar contraseñas de texto plano a bcrypt hash.
Ejecutar una sola vez después de actualizar el sistema de autenticación.
"""
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.backend.database import engine, init_db
from app.backend.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def migrate_passwords():
    """Migrar todas las contraseñas de texto plano a bcrypt hash"""
    init_db()
    
    with Session(engine) as session:
        # Obtener todos los usuarios
        statement = select(User)
        users = session.exec(statement).all()
        
        migrated = 0
        already_hashed = 0
        
        for user in users:
            try:
                # Intentar verificar si ya es un hash válido
                pwd_context.identify(user.password)
                already_hashed += 1
                print(f"✓ {user.email} - Ya tiene hash bcrypt")
            except Exception:
                # No es un hash válido, es texto plano
                print(f"⚠ {user.email} - Migrando contraseña de texto plano...")
                
                # Truncar password a 72 bytes (limitación de bcrypt)
                password_bytes = user.password.encode('utf-8')
                if len(password_bytes) > 72:
                    password = password_bytes[:72].decode('utf-8', errors='ignore')
                else:
                    password = user.password
                
                # Hashear la contraseña
                user.password = pwd_context.hash(password)
                session.add(user)
                migrated += 1
        
        if migrated > 0:
            session.commit()
            print(f"\n✅ Migración completada:")
            print(f"   - {migrated} contraseñas migradas a bcrypt")
            print(f"   - {already_hashed} ya estaban hasheadas")
        else:
            print(f"\n✅ Todas las contraseñas ({already_hashed}) ya están hasheadas correctamente")


if __name__ == "__main__":
    print("🔐 Iniciando migración de contraseñas a bcrypt...\n")
    migrate_passwords()
