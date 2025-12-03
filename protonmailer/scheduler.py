import logging
from datetime import datetime, timezone
from typing import Sequence

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from sqlalchemy.orm import Session

from protonmailer.database import SessionLocal
from protonmailer.models import Account, Campaign, Contact, QueuedEmail, Template
from protonmailer.services.email_service import send_email
from protonmailer.services.template_service import render_template

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def _get_due_emails(session: Session, now: datetime) -> Sequence[QueuedEmail]:
    return (
        session.query(QueuedEmail)
        .filter(QueuedEmail.status == "queued", QueuedEmail.scheduled_for <= now)
        .all()
    )


def process_queued_emails() -> None:
    session = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        queued_emails = _get_due_emails(session, now)
        for email in queued_emails:
            logger.info("Processing queued email %s", email.id)
            email.status = "sending"
            session.commit()
            session.refresh(email)

            account = session.query(Account).filter(Account.id == email.account_id).first()
            if not account:
                email.status = "failed"
                email.last_error = "Account not found"
                session.commit()
                continue

            to_addresses = [addr.strip() for addr in email.to_address.split(",") if addr.strip()]
            try:
                success, error = send_email(
                    account=account,
                    to_addresses=to_addresses or email.to_address,
                    subject=email.subject,
                    body_html=email.body_html,
                    body_text=email.body_text,
                )
            except Exception as exc:  # pragma: no cover - defensive catch
                logger.exception("Unexpected error while sending email %s", email.id)
                success = False
                error = str(exc)

            if success:
                email.status = "sent"
                email.sent_at = datetime.now(timezone.utc)
                email.last_error = None
                logger.info("Queued email %s sent successfully", email.id)
            else:
                email.status = "failed"
                email.last_error = error
                logger.error("Failed to send queued email %s: %s", email.id, error)

            session.commit()
    finally:
        session.close()


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            logger.warning("Invalid datetime format in schedule_config: %s", value)
            return None
    return None


def _should_run_campaign(campaign: Campaign, now: datetime) -> bool:
    config = campaign.schedule_config or {}

    if campaign.schedule_type == "one_time":
        run_at = _parse_datetime(config.get("run_at"))
        if not run_at:
            return False
        return campaign.last_run_at is None and now >= run_at

    if campaign.schedule_type == "recurring" and config.get("freq") == "daily":
        hour = int(config.get("hour", 0) or 0)
        minute = int(config.get("minute", 0) or 0)
        scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        last_run_date = campaign.last_run_at.date() if campaign.last_run_at else None
        return now >= scheduled_time and last_run_date != now.date()

    return False


def _tags_list(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [t.strip().lower() for t in tags.split(",") if t.strip()]


def _contact_matches(contact: Contact, target_tags: list[str]) -> bool:
    if not target_tags:
        return True
    contact_tags = ",".join(_tags_list(contact.tags))
    return any(tag in contact_tags for tag in target_tags)


def _build_contact_context(contact: Contact) -> dict[str, str | None]:
    first_name = None
    last_name = None
    if contact.name:
        parts = contact.name.split()
        if parts:
            first_name = parts[0]
            last_name = " ".join(parts[1:]) if len(parts) > 1 else None

    return {
        "name": contact.name,
        "email": contact.email,
        "first_name": first_name,
        "last_name": last_name,
    }


def run_campaigns() -> None:
    session = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        campaigns = session.query(Campaign).filter(Campaign.active.is_(True)).all()
        for campaign in campaigns:
            if not _should_run_campaign(campaign, now):
                continue

            logger.info("Running campaign %s", campaign.id)
            account = session.query(Account).filter(Account.id == campaign.account_id).first()
            template = session.query(Template).filter(Template.id == campaign.template_id).first()
            if not account or not template:
                logger.error("Campaign %s skipped due to missing account or template", campaign.id)
                campaign.last_run_at = now
                session.commit()
                continue

            target_tags = _tags_list(campaign.target_tags)
            contacts = session.query(Contact).all()
            for contact in contacts:
                if not _contact_matches(contact, target_tags):
                    continue

                context = _build_contact_context(contact)
                subject, body_html = render_template(template, context)
                queued_email = QueuedEmail(
                    campaign_id=campaign.id,
                    account_id=campaign.account_id,
                    from_address=account.email_address,
                    to_address=contact.email,
                    subject=subject,
                    body_html=body_html,
                    body_text=template.body_text,
                    scheduled_for=now,
                    status="queued",
                )
                session.add(queued_email)

            campaign.last_run_at = now
            session.commit()
            logger.info("Campaign %s enqueued emails at %s", campaign.id, now.isoformat())
    except Exception:  # pragma: no cover - defensive catch
        logger.exception("Unexpected error while running campaigns")
    finally:
        session.close()


def start_scheduler(app: FastAPI) -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        process_queued_emails,
        "interval",
        seconds=60,
        id="process_queued_emails",
        replace_existing=True,
    )
    scheduler.add_job(
        run_campaigns,
        "interval",
        seconds=60,
        id="run_campaigns",
        replace_existing=True,
    )
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("Scheduler started with campaign runner and queued email processor")
