from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

from app.backend.database import init_db
from app.backend.routers import auth_router, dashboard_router

app = FastAPI(debug=True)

app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")

templates = Jinja2Templates(directory="app/frontend/templates")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/login")


app.include_router(auth_router)
app.include_router(dashboard_router)