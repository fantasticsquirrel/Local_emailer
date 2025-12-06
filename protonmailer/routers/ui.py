import calendar
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from protonmailer import models
from protonmailer.dependencies import get_db
from protonmailer.services.auth_service import login_user, logout_user, require_login

router = APIRouter(prefix="/ui", tags=["ui"])
templates = Jinja2Templates(directory="templates")


def _split_addresses(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.replace(";", ",").split(",") if part.strip()]


def _add_months(base: datetime, months: int, day: int) -> datetime:
    month_index = base.month - 1 + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    target_day = min(max(day, 1), last_day)
    return base.replace(year=year, month=month, day=target_day)


def _calculate_step_time(previous: datetime, step: dict) -> datetime:
    offset_type = step.get("offset_type") or "immediate"
    if offset_type == "days":
        try:
            days = int(step.get("offset_value") or 0)
        except (TypeError, ValueError):
            days = 0
        return previous + timedelta(days=days)

    if offset_type == "monthly":
        try:
            day_of_month = int(step.get("day_of_month") or previous.day)
        except (TypeError, ValueError):
            day_of_month = previous.day
        try:
            month_interval = int(step.get("month_interval") or 1)
        except (TypeError, ValueError):
            month_interval = 1
        return _add_months(previous, month_interval, day_of_month)

    return previous


def _load_sequence_steps(payload: str | None, fallback_subject: str, fallback_body: str) -> list[dict]:
    try:
        raw_steps = json.loads(payload or "[]")
    except json.JSONDecodeError:
        raw_steps = []

    steps: list[dict] = []
    for step in raw_steps:
        subject = step.get("subject") or fallback_subject
        body = step.get("body") or fallback_body
        if not subject or not body:
            continue
        steps.append(
            {
                "subject": subject,
                "body": body,
                "offset_type": step.get("offset_type") or "immediate",
                "offset_value": step.get("offset_value"),
                "day_of_month": step.get("day_of_month"),
                "month_interval": step.get("month_interval"),
            }
        )

    if not steps:
        steps.append(
            {
                "subject": fallback_subject,
                "body": fallback_body,
                "offset_type": "immediate",
                "offset_value": 0,
            }
        )

    return steps


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


@router.get(
    "/contacts",
    response_class=HTMLResponse,
    name="contacts_list",
    dependencies=[Depends(require_login)],
)
def contacts_list(request: Request, db: Session = Depends(get_db)):
    contacts = db.query(models.Contact).order_by(models.Contact.created_at.desc()).all()
    return templates.TemplateResponse(
        "contacts_list.html", {"request": request, "contacts": contacts}
    )


@router.get(
    "/contacts/new",
    response_class=HTMLResponse,
    name="contact_new",
    dependencies=[Depends(require_login)],
)
async def contact_new(request: Request):
    return templates.TemplateResponse(
        "contact_form.html",
        {"request": request, "contact": None},
    )


@router.post(
    "/contacts/new",
    response_class=HTMLResponse,
    name="contact_create",
    dependencies=[Depends(require_login)],
)
async def contact_create(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    name = form.get("name") or ""
    email = form.get("email") or ""
    tags = form.get("tags") or ""

    if "@" not in email:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Invalid email"},
            status_code=400,
        )

    contact = models.Contact(name=name, email=email, tags=tags)
    db.add(contact)
    db.commit()

    return RedirectResponse(request.url_for("contacts_list"), status_code=303)


@router.get(
    "/contacts/{contact_id}/edit",
    response_class=HTMLResponse,
    name="contact_edit",
    dependencies=[Depends(require_login)],
)
async def contact_edit(contact_id: int, request: Request, db: Session = Depends(get_db)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if contact is None:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Contact not found"},
            status_code=404,
        )
    return templates.TemplateResponse(
        "contact_form.html",
        {"request": request, "contact": contact},
    )


@router.post(
    "/contacts/{contact_id}/edit",
    response_class=HTMLResponse,
    name="contact_update",
    dependencies=[Depends(require_login)],
)
async def contact_update(contact_id: int, request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    name = form.get("name") or ""
    email = form.get("email") or ""
    tags = form.get("tags") or ""

    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if contact is None:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Contact not found"},
            status_code=404,
        )

    contact.name = name
    contact.email = email
    contact.tags = tags
    db.commit()

    return RedirectResponse(request.url_for("contacts_list"), status_code=303)


@router.post(
    "/contacts/{contact_id}/delete",
    response_class=HTMLResponse,
    name="contact_delete",
    dependencies=[Depends(require_login)],
)
async def contact_delete(contact_id: int, request: Request, db: Session = Depends(get_db)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if contact:
        db.delete(contact)
        db.commit()
    return RedirectResponse(request.url_for("contacts_list"), status_code=303)


@router.get(
    "/campaigns",
    response_class=HTMLResponse,
    name="campaigns_list",
    dependencies=[Depends(require_login)],
)
async def campaigns_list(request: Request, db: Session = Depends(get_db)):
    campaigns = db.query(models.Campaign).order_by(models.Campaign.created_at.desc()).all()
    return templates.TemplateResponse(
        "campaigns_list.html",
        {"request": request, "campaigns": campaigns},
    )


@router.get(
    "/campaigns/new",
    response_class=HTMLResponse,
    name="campaign_new",
    dependencies=[Depends(require_login)],
)
async def campaign_new(request: Request, db: Session = Depends(get_db)):
    accounts = db.query(models.Account).all()
    templates_list = db.query(models.Template).all()
    return templates.TemplateResponse(
        "campaign_form.html",
        {
            "request": request,
            "campaign": None,
            "accounts": accounts,
            "templates": templates_list,
        },
    )


@router.post(
    "/campaigns/new",
    response_class=HTMLResponse,
    name="campaign_create",
    dependencies=[Depends(require_login)],
)
async def campaign_create(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    name = form.get("name") or ""
    account_id = int(form.get("account_id"))
    template_id = int(form.get("template_id"))
    target_tags = form.get("target_tags") or ""
    schedule_type = form.get("schedule_type") or "one_time"
    active = form.get("active") == "on"

    run_date = form.get("run_date") or ""
    run_time = form.get("run_time") or ""
    freq = form.get("freq") or "once"
    day_of_week = form.get("day_of_week") or None

    schedule_config = {
        "freq": freq,
        "run_date": run_date,
        "run_time": run_time,
        "day_of_week": day_of_week,
    }

    campaign = models.Campaign(
        name=name,
        account_id=account_id,
        template_id=template_id,
        target_tags=target_tags,
        schedule_type=schedule_type,
        schedule_config=json.dumps(schedule_config),
        active=active,
    )
    db.add(campaign)
    db.commit()

    return RedirectResponse(request.url_for("campaigns_list"), status_code=303)


@router.get(
    "/campaigns/{campaign_id}/edit",
    response_class=HTMLResponse,
    name="campaign_edit",
    dependencies=[Depends(require_login)],
)
async def campaign_edit(campaign_id: int, request: Request, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Campaign not found"},
            status_code=404,
        )
    accounts = db.query(models.Account).all()
    templates_list = db.query(models.Template).all()

    try:
        schedule_config = json.loads(campaign.schedule_config or "{}")
    except json.JSONDecodeError:
        schedule_config = {}

    return templates.TemplateResponse(
        "campaign_form.html",
        {
            "request": request,
            "campaign": campaign,
            "accounts": accounts,
            "templates": templates_list,
            "schedule_config": schedule_config,
        },
    )


@router.post(
    "/campaigns/{campaign_id}/edit",
    response_class=HTMLResponse,
    name="campaign_update",
    dependencies=[Depends(require_login)],
)
async def campaign_update(campaign_id: int, request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    name = form.get("name") or ""
    account_id = int(form.get("account_id"))
    template_id = int(form.get("template_id"))
    target_tags = form.get("target_tags") or ""
    schedule_type = form.get("schedule_type") or "one_time"
    active = form.get("active") == "on"

    run_date = form.get("run_date") or ""
    run_time = form.get("run_time") or ""
    freq = form.get("freq") or "once"
    day_of_week = form.get("day_of_week") or None

    schedule_config = {
        "freq": freq,
        "run_date": run_date,
        "run_time": run_time,
        "day_of_week": day_of_week,
    }

    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Campaign not found"},
            status_code=404,
        )

    campaign.name = name
    campaign.account_id = account_id
    campaign.template_id = template_id
    campaign.target_tags = target_tags
    campaign.schedule_type = schedule_type
    campaign.schedule_config = json.dumps(schedule_config)
    campaign.active = active
    db.commit()

    return RedirectResponse(request.url_for("campaigns_list"), status_code=303)


@router.post(
    "/campaigns/{campaign_id}/activate",
    response_class=HTMLResponse,
    name="campaign_activate",
    dependencies=[Depends(require_login)],
)
async def campaign_activate(campaign_id: int, request: Request, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if campaign:
        campaign.active = True
        db.commit()
    return RedirectResponse(request.url_for("campaigns_list"), status_code=303)


@router.post(
    "/campaigns/{campaign_id}/deactivate",
    response_class=HTMLResponse,
    name="campaign_deactivate",
    dependencies=[Depends(require_login)],
)
async def campaign_deactivate(campaign_id: int, request: Request, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if campaign:
        campaign.active = False
        db.commit()
    return RedirectResponse(request.url_for("campaigns_list"), status_code=303)


@router.get(
    "/queue",
    response_class=HTMLResponse,
    name="queue_list",
    dependencies=[Depends(require_login)],
)
def queue_list(request: Request, db: Session = Depends(get_db)):
    emails = (
        db.query(models.QueuedEmail)
        .order_by(models.QueuedEmail.created_at.desc())
        .limit(200)
        .all()
    )
    return templates.TemplateResponse(
        "queue_list.html", {"request": request, "emails": emails}
    )


@router.post(
    "/queue/{email_id}/cancel",
    response_class=HTMLResponse,
    name="queue_cancel",
    dependencies=[Depends(require_login)],
)
def queue_cancel(email_id: int, request: Request, db: Session = Depends(get_db)):
    qe = db.query(models.QueuedEmail).filter(models.QueuedEmail.id == email_id).first()
    if qe and qe.status == "queued":
        qe.status = "cancelled"
        db.commit()
    return RedirectResponse(request.url_for("queue_list"), status_code=303)


@router.post(
    "/queue/{email_id}/retry",
    response_class=HTMLResponse,
    name="queue_retry",
    dependencies=[Depends(require_login)],
)
def queue_retry(email_id: int, request: Request, db: Session = Depends(get_db)):
    qe = db.query(models.QueuedEmail).filter(models.QueuedEmail.id == email_id).first()
    if qe and qe.status == "failed":
        qe.status = "queued"
        qe.last_error = None
        qe.scheduled_for = datetime.utcnow()
        db.commit()
    return RedirectResponse(request.url_for("queue_list"), status_code=303)


@router.get(
    "/compose",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def compose_email(request: Request, db: Session = Depends(get_db)):
    accounts = db.query(models.Account).all()
    templates_list = db.query(models.Template).all()
    contacts = db.query(models.Contact).order_by(models.Contact.name.asc()).all()
    return templates.TemplateResponse(
        "email_compose.html",
        {
            "request": request,
            "accounts": accounts,
            "templates": templates_list,
            "contacts": contacts,
        },
    )


@router.post(
    "/compose",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def submit_compose_email(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    account_id = int(form.get("account_id"))
    subject = form.get("subject") or ""
    body = form.get("body") or ""
    template_id = form.get("template_id") or None
    send_now = form.get("send_now") == "on"
    send_date = form.get("send_date") or ""
    send_time = form.get("send_time") or ""
    sequence_payload = form.get("sequence_payload") or "[]"
    manual_to = form.get("to_manual") or ""
    selected_contacts = form.getlist("to_contacts")

    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if account is None:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Account not found"},
            status_code=400,
        )

    if template_id:
        template = (
            db.query(models.Template).filter(models.Template.id == int(template_id)).first()
        )
        if template:
            subject = subject or template.subject
            body = body or template.body_html

    if send_now:
        scheduled_for = datetime.utcnow()
    else:
        if send_date and send_time:
            scheduled_for = datetime.fromisoformat(f"{send_date}T{send_time}")
        else:
            scheduled_for = datetime.utcnow()

    contact_ids = []
    for cid in selected_contacts:
        try:
            contact_ids.append(int(cid))
        except ValueError:
            continue

    contacts = (
        db.query(models.Contact)
        .filter(models.Contact.id.in_(contact_ids))
        .order_by(models.Contact.id.asc())
        .all()
        if contact_ids
        else []
    )

    to_addresses = []
    seen = set()
    for contact in contacts:
        if contact.email not in seen:
            to_addresses.append(contact.email)
            seen.add(contact.email)

    for addr in _split_addresses(manual_to):
        if addr not in seen:
            to_addresses.append(addr)
            seen.add(addr)

    if not to_addresses:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "No recipients selected"},
            status_code=400,
        )

    steps = _load_sequence_steps(sequence_payload, subject, body)

    from_address = account.email_address

    created_count = 0
    current_send_time = scheduled_for
    for index, step in enumerate(steps, start=1):
        if step.get("offset_type") != "immediate":
            current_send_time = _calculate_step_time(current_send_time, step)

        for addr in to_addresses:
            qe = models.QueuedEmail(
                campaign_id=None,
                account_id=account.id,
                from_address=from_address,
                to_address=addr,
                subject=step.get("subject") or subject,
                body_html=step.get("body") or body,
                body_text=None,
                scheduled_for=current_send_time,
                status="queued",
                source="manual",
                metadata_json=json.dumps(
                    {
                        "sequence_step": index,
                        "offset_type": step.get("offset_type"),
                        "offset_value": step.get("offset_value"),
                        "month_interval": step.get("month_interval"),
                        "day_of_month": step.get("day_of_month"),
                    }
                ),
            )
            db.add(qe)
            created_count += 1

    db.commit()

    url = request.url_for("queue_list")
    response = RedirectResponse(url, status_code=303)
    return response
