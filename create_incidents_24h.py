"""
Script para crear incidentes de prueba con fechas de las últimas 24 horas
"""
from datetime import datetime, timedelta
import random
from sqlmodel import Session, create_engine, select
from app.backend.models.incident import Incident
from app.backend.models.user import User

# Conectar a la base de datos
engine = create_engine("sqlite:///cyberwatch.db")

# Datos de ejemplo
titles = [
    "Acceso no autorizado a servidor de archivos",
    "Detección de malware en estación de trabajo",
    "Intento de phishing reportado por usuario",
    "Tráfico sospechoso hacia dominio externo",
    "Actividad anómala en cuenta de administrador",
    "Escaneo de puertos detectado en red interna",
    "Ransomware bloqueado por EDR",
    "Exfiltración de datos potencial detectada",
    "Credenciales comprometidas en Dark Web",
    "Ataque DDoS en servidor web",
    "Inyección SQL bloqueada en aplicación web",
    "Modificación no autorizada de archivos críticos",
    "Proceso sospechoso ejecutado en servidor",
    "Múltiples intentos de inicio de sesión fallidos",
    "Dispositivo USB no autorizado conectado",
    "Tráfico cifrado inusual detectado",
    "Cambio de permisos no autorizado en Active Directory",
    "Comunicación con servidor C2 detectada",
    "Vulnerabilidad crítica detectada en sistema",
    "Acceso SSH desde ubicación inusual",
    "Movimiento lateral detectado en la red",
    "Ejecución de script PowerShell sospechoso",
    "Archivo malicioso en correo electrónico bloqueado"
]

descriptions = [
    "Se detectó un acceso no autorizado utilizando credenciales válidas fuera del horario laboral.",
    "El EDR identificó un archivo ejecutable sospechoso que intentaba establecer persistencia.",
    "Usuario reportó correo electrónico con enlace sospechoso simulando ser del departamento de IT.",
    "El firewall registró múltiples conexiones salientes a un dominio de reputación dudosa.",
    "Se observó actividad inusual en cuenta con privilegios elevados durante horas no habituales.",
    "NMAP detectó escaneo de puertos TCP en rango de servidores críticos.",
    "El antivirus bloqueó un intento de cifrado masivo de archivos en directorio compartido.",
    "Se detectó transferencia de gran volumen de datos hacia servicios cloud no autorizados.",
    "Monitoreo de Dark Web identificó credenciales corporativas en venta en foro underground.",
    "Servidor web experimentó súbito incremento de tráfico desde múltiples IPs distribuidas.",
    "WAF bloqueó múltiples intentos de inyección SQL en formulario de login de aplicación.",
    "Sistema de integridad detectó modificación de archivos de configuración en servidor.",
    "Análisis de comportamiento identificó proceso desconocido consumiendo recursos anormales.",
    "Sistema detectó 47 intentos fallidos de autenticación desde IPs internacionales.",
    "DLP alertó sobre conexión de dispositivo de almacenamiento no registrado en política.",
    "Análisis de red identificó tráfico TLS anómalo con certificado auto-firmado sospechoso.",
    "Auditoría de AD reveló modificación de permisos de grupo sin ticket de cambio aprobado.",
    "IDS identificó patrón de comunicación característico de malware conocido hacia IP externa.",
    "Escaneo de vulnerabilidades identificó CVE crítico sin parche en servidor expuesto.",
    "Sistema SIEM correlacionó acceso SSH desde país no habitual con horario inusual.",
    "EDR detectó intentos de conexión RDP desde estación comprometida hacia múltiples servidores.",
    "Script PowerShell obfuscado intentó descargar payload desde dominio recién registrado.",
    "Gateway de correo bloqueó adjunto con extensión doble y contenido malicioso confirmado."
]

severities = ["Bajo", "Medio", "Alto", "Crítico"]
statuses = ["Abierto", "En investigación", "Asignado", "Mitigado", "Cerrado"]
sources = ["EDR", "Firewall", "SIEM", "Alerta SIEM", "Correo", "Usuario", "Detección automática"]

# Crear sesión
with Session(engine) as session:
    # Obtener usuarios activos de la base de datos
    statement = select(User).where(User.is_active == True)
    active_users = list(session.exec(statement).all())
    
    if not active_users:
        print("❌ Error: No hay usuarios activos en la base de datos.")
        print("   Crea usuarios primero usando: python create_user.py")
        exit(1)
    
    # Crear lista de posibles responsables (usuarios activos + None para sin asignar)
    owners = [user.full_name for user in active_users] + [None, None]  # Dos None para mayor probabilidad de sin asignar
    
    print(f"📊 Usuarios activos encontrados: {len(active_users)}")
    for user in active_users:
        print(f"   - {user.full_name} ({user.email})")
    print()
    
    # Obtener el último número de incidente del año actual
    current_year = datetime.now().year
    statement = select(Incident).where(
        Incident.code.like(f"INC-{current_year}-%")
    ).order_by(Incident.code.desc())
    
    last_incident = session.exec(statement).first()
    
    if last_incident and last_incident.code:
        try:
            last_number = int(last_incident.code.split('-')[-1])
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1
    
    # Hora actual
    now = datetime.now()
    
    # Crear 23 incidentes
    print("🔄 Creando incidentes...")
    for i in range(23):
        # Generar fecha aleatoria en las últimas 24 horas
        hours_ago = random.uniform(0, 24)
        detected_at = now - timedelta(hours=hours_ago)
        
        # Crear código de incidente
        code = f"INC-{current_year}-{next_number:04d}"
        next_number += 1
        
        # Seleccionar responsable aleatorio
        owner = random.choice(owners)
        
        # Crear incidente
        incident = Incident(
            code=code,
            title=titles[i],
            description=descriptions[i],
            severity=random.choice(severities),
            status=random.choice(statuses),
            source=random.choice(sources),
            owner=owner,
            detected_at=detected_at,
            updated_at=detected_at
        )
        
        session.add(incident)
        owner_display = owner if owner else "Sin asignar"
        print(f"✓ {code} - {incident.title[:50]}... → {owner_display} ({detected_at.strftime('%Y-%m-%d %H:%M')})")
    
    session.commit()
    print(f"\n✅ Se crearon 23 incidentes exitosamente con fechas de las últimas 24 horas")
