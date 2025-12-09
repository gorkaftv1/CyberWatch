# CyberWatch - Sistema de Gestión de Incidentes de Seguridad

## 📋 Descripción

CyberWatch es una aplicación web profesional para la gestión de incidentes de ciberseguridad, diseñada para equipos SOC (Security Operations Center). Permite el registro, seguimiento, asignación y análisis de incidentes de seguridad de manera eficiente y organizada, con un sistema robusto de gestión de logs, autenticación segura y modales personalizados para una experiencia de usuario profesional.

## 🚀 Tecnologías Utilizadas

### Backend
- **FastAPI 0.115.5** - Framework web moderno y de alto rendimiento para Python
- **SQLModel 0.0.22** - ORM basado en SQLAlchemy con integración de Pydantic para validación de datos
- **Uvicorn 0.32.1** - Servidor ASGI de alto rendimiento
- **Passlib[bcrypt] 1.7.4 + Bcrypt 4.0.1** - Sistema de hash de contraseñas seguro con migración automática
- **Python-multipart 0.0.20** - Manejo de formularios multipart

### Frontend
- **Jinja2 3.1.4** - Motor de plantillas para renderizado server-side
- **HTML5 + CSS3** - Estructura y estilos modernos con tema oscuro profesional
- **JavaScript Vanilla** - Interactividad del lado del cliente sin dependencias
- **Diseño responsive** - Interfaz adaptable a diferentes dispositivos
- **Sistema de modales personalizados** - Confirmaciones profesionales con animaciones

### Base de Datos
- **SQLite** - Base de datos relacional embebida (por defecto)
- Compatible con PostgreSQL, MySQL u otros motores SQL

## 📊 Estructura de la Base de Datos

### Tabla: `incident`
Almacena la información de los incidentes de seguridad.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer (PK) | Identificador único del incidente |
| `code` | String (Unique) | Código del incidente (ej: INC-2025-0001) |
| `title` | String | Título descriptivo del incidente |
| `description` | Text | Descripción detallada del incidente |
| `severity` | String | Nivel de severidad: Bajo, Medio, Alto, Crítico |
| `status` | String | Estado: Abierto, En investigación, Asignado, Mitigado, Cerrado |
| `source` | String | Origen de detección: EDR, Firewall, SIEM, Correo, Usuario, etc. |
| `owner` | String | Analista responsable del incidente |
| `detected_at` | DateTime | Fecha y hora de detección |
| `created_at` | DateTime | Fecha y hora de creación del registro |
| `updated_at` | DateTime | Fecha y hora de última actualización |

### Tabla: `user`
Almacena la información de los usuarios del sistema.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer (PK) | Identificador único del usuario |
| `email` | String (Unique) | Correo electrónico del usuario |
| `password` | String | Contraseña hasheada con bcrypt |
| `full_name` | String | Nombre completo del usuario |
| `is_active` | Boolean | Estado del usuario (activo/inactivo) |
| `role` | String | Rol: analyst o admin |

### Tabla: `incidentattachment`
Almacena archivos de logs (texto plano) asociados a incidentes.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer (PK) | Identificador único del attachment |
| `incident_id` | Integer (FK) | ID del incidente relacionado |
| `filename` | String | Nombre del archivo subido (.txt) |
| `content` | Text | Contenido completo del archivo en texto plano |
| `uploaded_at` | DateTime | Fecha y hora de subida |

## 🏗️ Arquitectura del Proyecto

```
CyberWatch/
├── app/
│   ├── __init__.py
│   ├── main.py                      # Punto de entrada de la aplicación
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── database.py              # Configuración de la base de datos
│   │   ├── core/                    # Configuraciones centrales
│   │   ├── dependencies/
│   │   │   └── auth.py              # Dependencias de autenticación
│   │   ├── models/
│   │   │   ├── incident.py          # Modelo de incidente
│   │   │   ├── incident_attachment.py # Modelo de logs adjuntos
│   │   │   └── user.py              # Modelo de usuario
│   │   ├── repositories/
│   │   │   ├── incident_repository.py  # Operaciones CRUD de incidentes
│   │   │   ├── incident_attachment_repository.py # CRUD de logs
│   │   │   └── user_repository.py      # Operaciones CRUD de usuarios
│   │   └── routers/
│   │       ├── auth.py              # Rutas de autenticación
│   │       ├── dashboard.py         # Rutas del dashboard
│   │       ├── incidents.py         # Rutas de incidentes
│   │       └── users.py             # Rutas de usuarios (admin)
│   └── frontend/
│       ├── static/
│       │   ├── css/
│       │   │   └── style.css        # Estilos de la aplicación
│       │   ├── images/              # Recursos gráficos
│       │   └── js/
│       │       └── login.js         # Scripts de login
│       └── templates/
│           ├── base.html            # Plantilla base
│           ├── login.html           # Página de inicio de sesión
│           ├── dashboard.html       # Dashboard principal
│           ├── incidents.html       # Lista de incidentes
│           ├── incident_detail.html # Detalle de incidente
│           ├── incident_form.html   # Formulario de incidente
│           ├── users.html           # Lista de usuarios (admin)
│           └── user_form.html       # Formulario de usuario (admin)
├── create_incidents.py              # Script de creación de incidentes
├── create_user.py                   # Script de creación de usuarios
├── migrate_passwords.py             # Script de migración de contraseñas
├── requirements.txt                 # Dependencias del proyecto
└── README.md                        # Este archivo
```

## 🔧 Instalación y Configuración

### Requisitos Previos
- Python 3.11 o superior
- pip o conda

### Instalación con pip

1. **Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd CyberWatch
```

2. **Crear entorno virtual (recomendado)**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install fastapi uvicorn[standard] sqlmodel passlib[bcrypt] python-multipart jinja2
```

O usando el archivo requirements.txt:
```bash
pip install -r requirements.txt
```

### Instalación con Conda

```bash
conda create -n cyberwatch python=3.11
conda activate cyberwatch
pip install fastapi uvicorn[standard] sqlmodel passlib[bcrypt] python-multipart jinja2
```

## 🚀 Ejecución

### Iniciar el servidor de desarrollo

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La aplicación estará disponible en: `http://localhost:8000`

### Crear usuarios iniciales

Para crear un usuario administrador:
```bash
python create_user.py
```

Sigue las instrucciones para ingresar:
- Email
- Nombre completo
- Contraseña
- Rol (admin o analyst)

### Crear incidentes de prueba

Para poblar la base de datos con incidentes de ejemplo:
```bash
python create_incidents.py
```

## 👤 Sistema de Usuarios y Roles

### Roles disponibles

1. **Analista (analyst)**
   - Ver dashboard
   - Ver lista de incidentes (con filtro automático por analista asignado, removible)
   - Ver detalles de incidentes
   - Crear nuevos incidentes
   - Editar incidentes
   - Gestionar logs de incidentes (subir, visualizar, eliminar archivos .txt)
   - Exportar incidentes a CSV

2. **Administrador (admin)**
   - Todas las funcionalidades del analista
   - Gestionar usuarios (crear, editar, eliminar con modales de confirmación)
   - Acceso a la sección de administración de usuarios
   - Vista completa de todos los incidentes sin filtros por defecto

## 📱 Funcionalidades Principales

### Dashboard
- Visión general de incidentes
- KPIs principales:
  - Incidentes abiertos
  - Incidentes críticos
  - MTTR (Mean Time To Resolve)
  - Alertas del día
- Gráfico de distribución por severidad
- Lista de incidentes recientes
- Actividad reciente
- Botón de acceso rápido para crear incidentes

### Gestión de Incidentes
- **Lista de incidentes** con:
  - Filtros avanzados (severidad, estado, origen, responsable)
  - **Filtro automático para analistas**: Los analistas ven por defecto solo sus incidentes asignados, con indicador visual (estrella amarilla) que puede ser removido para ver todos
  - Búsqueda por texto (código, título, descripción)
  - Paginación configurable (10, 25 o 100 elementos)
  - Exportación a CSV respetando filtros aplicados
  - Vista de tabla con información clave y badges de estado
- **Formulario de creación/edición**:
  - Código de incidente autogenerado
  - Título y descripción detallada
  - Nivel de severidad (Bajo, Medio, Alto, Crítico)
  - Estado del incidente (Abierto, En investigación, Asignado, Mitigado, Cerrado)
  - Origen de detección (EDR, Firewall, SIEM, Correo, Usuario, etc.)
  - Asignación a analista (desplegable con usuarios activos)
  - **Sección de Logs del Incidente**:
    - Subida de archivos de log (.txt únicamente)
    - Visualización expandible del contenido con contador de líneas
    - Eliminación de logs con modal de confirmación personalizado
- **Vista detallada**:
  - Información completa del incidente con timestamps
  - Gestión completa de logs adjuntos
  - Acciones disponibles (editar, eliminar)
  - **Modal de eliminación personalizado**: Confirmación profesional con animaciones y bloqueo de interacción

### Gestión de Usuarios (Solo Administradores)
- Lista de usuarios registrados con información detallada
- Creación de nuevos usuarios con validación de contraseña
- Edición de usuarios existentes
- Activación/desactivación de usuarios
- **Modal de eliminación personalizado**:
  - Confirmación mostrando nombre y email del usuario
  - Diseño consistente con modal de eliminación de incidentes
  - Protección para auto-eliminación
  - Animaciones y bloqueo de interacción
- Cambio de roles (analyst/admin)
- Contraseñas automáticamente truncadas a 72 bytes para compatibilidad con bcrypt

### Autenticación
- Sistema de login seguro con bcrypt
- **Migración automática de contraseñas**: Si un usuario tiene contraseña en texto plano, se convierte automáticamente a bcrypt en el primer login
- Sesiones basadas en cookies seguras
- Protección de rutas por autenticación
- Control de acceso basado en roles (analyst/admin)
- Hash de contraseñas con factor de trabajo 12
- Script de migración masiva disponible (migrate_passwords.py)

### Exportación
- Exportación de incidentes a formato CSV
- Respeta los filtros aplicados
- Incluye todos los campos relevantes

## 🎨 Características de la Interfaz

- **Diseño moderno** con tema oscuro profesional (#1a1d29)
- **Sistema de modales personalizados**:
  - Diseño con gradientes y sombras profesionales
  - Backdrop blur para enfocar la atención
  - Animaciones de entrada (fadeIn para overlay, popIn con scale para modal)
  - Bloqueo completo de interacción con el contenido subyacente
  - Cierre con tecla ESC
  - Iconos de advertencia con color temático (#dc2626)
- **Totalmente responsive** - se adapta a móviles, tablets y desktop
- **Navegación intuitiva** con sidebar siempre visible
- **Feedback visual** con estados hover, active y disabled
- **Animaciones suaves** para mejorar la experiencia de usuario
- **Iconos SVG** para mejor rendimiento
- **Scrollbars personalizados** para mantener la estética
- **Badges de estado** con colores diferenciados por severidad y estado
- **Indicadores visuales**: Filtros activos, líneas de log, estados de carga

## 🔒 Seguridad

- **Contraseñas hasheadas con bcrypt** (factor de trabajo 12, bcrypt 4.0.1)
- **Migración automática de contraseñas antiguas**: Sistema transparente que convierte contraseñas en texto plano a bcrypt en el primer login
- **Truncamiento automático de contraseñas a 72 bytes**: Garantiza compatibilidad con bcrypt
- Protección contra inyección SQL (uso de ORM SQLModel)
- Validación de entrada en formularios
- Control de acceso basado en roles con decoradores
- Sesiones seguras con cookies HttpOnly
- Protección CSRF en formularios
- **Archivos de log**: Solo acepta archivos .txt, almacenados como texto plano en base de datos

## 📈 Características Técnicas

### Patrón de Arquitectura
- **Repository Pattern** para abstracción de datos
- **Dependency Injection** con FastAPI
- **Separación de responsabilidades** (backend/frontend)
- **Modelos de dominio** con SQLModel

### Rendimiento
- Consultas optimizadas con paginación
- Índices en campos clave (email, code)
- Carga lazy de relaciones
- Renderizado server-side eficiente

### Escalabilidad
- Arquitectura modular y extensible
- Fácil migración a PostgreSQL/MySQL
- Preparado para caché (Redis)
- Posibilidad de API REST completa

## 🛠️ Desarrollo

### Scripts Útiles

**Crear usuario:**
```bash
python create_user.py
```

**Crear incidentes de prueba:**
```bash
python create_incidents.py
```

**Migrar contraseñas a bcrypt:**
```bash
python migrate_passwords.py
```

**Iniciar en modo desarrollo:**
```bash
python -m uvicorn app.main:app --reload
```

## 👥 Autores

- **Grupo 6 - SIO (GII)**: Eduardo Marrero Gonzalez, Jaime Calzada Sánchez, Gorka Eymard Santana Cabrera 
