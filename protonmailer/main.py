import logging

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from protonmailer.config import get_settings
from protonmailer.dependencies import get_db
from protonmailer.database import init_db
from protonmailer.routers import accounts, campaigns, contacts, templates, ui
from protonmailer.scheduler import start_scheduler
from protonmailer.services.auth_service import require_login

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("protonmailer")

settings = get_settings()

app = FastAPI(title="protonmailer")
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)

# Bind the app locally; intended for development use on 127.0.0.1
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    start_scheduler(app)


@app.get("/health")
def read_health(db: Session = Depends(get_db)) -> dict[str, str]:
    return {"status": "ok", "env": settings.ENV}


@app.get("/", include_in_schema=False)
def dashboard_root(
    request: Request,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(require_login),
):
    return ui.render_dashboard(request, db)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, StarletteHTTPException):
        raise exc

    logger.exception("Unhandled exception occurred")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(accounts.router)
app.include_router(contacts.router)
app.include_router(templates.router)
app.include_router(campaigns.router)
app.include_router(ui.router)
