from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from protonmailer import models
from protonmailer.dependencies import get_db
from protonmailer.services.auth_service import login_user, logout_user, require_login

router = APIRouter(prefix="/ui", tags=["ui"])
templates = Jinja2Templates(directory="templates")


def render_dashboard(request: Request, db: Session):
    accounts_count = db.query(models.Account).count()
    contacts_count = db.query(models.Contact).count()
    campaigns_count = db.query(models.Campaign).count()
    queued_count = db.query(models.QueuedEmail).filter(models.QueuedEmail.status == "queued").count()
    sent_count = db.query(models.QueuedEmail).filter(models.QueuedEmail.status == "sent").count()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "accounts_count": accounts_count,
            "contacts_count": contacts_count,
            "campaigns_count": campaigns_count,
            "queued_count": queued_count,
            "sent_count": sent_count,
        },
    )


@router.get("/", response_class=HTMLResponse, include_in_schema=False, dependencies=[Depends(require_login)])
def dashboard(request: Request, db: Session = Depends(get_db)):
    return render_dashboard(request, db)


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse, include_in_schema=False)
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if login_user(request, username, password):
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    else:
        response = templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return response


@router.get("/logout", include_in_schema=False)
def logout(request: Request):
    logout_user(request)
    return RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/accounts", response_class=HTMLResponse, dependencies=[Depends(require_login)])
def accounts_list(request: Request, db: Session = Depends(get_db)):
    accounts = db.query(models.Account).all()
    return templates.TemplateResponse(
        "accounts_list.html", {"request": request, "accounts": accounts}
    )


@router.get("/contacts", response_class=HTMLResponse, dependencies=[Depends(require_login)])
def contacts_list(request: Request, db: Session = Depends(get_db)):
    contacts = db.query(models.Contact).all()
    return templates.TemplateResponse(
        "contacts_list.html", {"request": request, "contacts": contacts}
    )


@router.get("/campaigns", response_class=HTMLResponse, dependencies=[Depends(require_login)])
def campaigns_list(request: Request, db: Session = Depends(get_db)):
    campaigns = db.query(models.Campaign).all()
    return templates.TemplateResponse(
        "campaigns_list.html", {"request": request, "campaigns": campaigns}
    )


@router.get("/queue", response_class=HTMLResponse, dependencies=[Depends(require_login)])
def queue_list(request: Request, db: Session = Depends(get_db)):
    queued_emails = (
        db.query(models.QueuedEmail)
        .order_by(models.QueuedEmail.scheduled_for.desc())
        .all()
    )
    return templates.TemplateResponse(
        "queue_list.html", {"request": request, "queued_emails": queued_emails}
    )


@router.get("/failed", response_class=HTMLResponse, dependencies=[Depends(require_login)])
def failed_emails(request: Request, db: Session = Depends(get_db)):
    failed = (
        db.query(models.QueuedEmail)
        .filter(models.QueuedEmail.status == "failed")
        .order_by(models.QueuedEmail.scheduled_for.desc())
        .all()
    )
    return templates.TemplateResponse(
        "failed_list.html", {"request": request, "queued_emails": failed}
    )
