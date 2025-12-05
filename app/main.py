from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.backend.database import init_db
from app.backend.routers import auth_router, dashboard_router, incidents_router, users_router

app = FastAPI(
    title="CyberWatch API",
    description="""
    ## Sistema de Gestión de Incidentes de Ciberseguridad
    
    CyberWatch es una aplicación completa para la gestión de incidentes de seguridad,
    diseñada para equipos SOC (Security Operations Center).
    
    ### Características principales:
    * **Gestión de incidentes**: Crear, editar, eliminar y buscar incidentes
    * **Control de acceso**: Sistema de roles (Analista y Administrador)
    * **Filtrado avanzado**: Por severidad, estado, origen y responsable
    * **Paginación**: Visualización eficiente de grandes volúmenes de datos
    * **Exportación**: Exportar incidentes a formato CSV
    * **Gestión de usuarios**: Administración completa de usuarios (solo admin)
    * **Dashboard**: Visualización de KPIs y métricas importantes
    
    ### Roles:
    * **Analista**: Acceso a incidentes y dashboard
    * **Administrador**: Acceso completo incluyendo gestión de usuarios
    """,
    version="1.0.0",
    contact={
        "name": "Equipo CyberWatch",
        "email": "soporte@cyberwatch.com",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    debug=True
)

app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")

templates = Jinja2Templates(directory="app/frontend/templates")


@app.on_event("startup")
def startup():
    init_db()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejador personalizado para errores HTTP"""
    if exc.status_code == 401:
        return RedirectResponse(url="/login?error=session_expired", status_code=303)
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/login")


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(incidents_router)
app.include_router(users_router)