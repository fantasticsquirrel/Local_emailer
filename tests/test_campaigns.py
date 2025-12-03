from datetime import datetime, timedelta, timezone

from protonmailer import models
from protonmailer.database import SessionLocal
from protonmailer.scheduler import run_campaigns


def test_campaign_runner_enqueues_emails(client):
    account_payload = {
        "display_name": "Mailer",
        "email_address": "mailer@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "user",
        "smtp_password_encrypted": "pass",
        "use_ssl": False,
        "use_tls": True,
    }
    account_resp = client.post("/accounts/", json=account_payload)
    account_id = account_resp.json()["id"]

    template_payload = {
        "name": "Welcome",
        "subject": "Hello {{ name }}",
        "body_html": "<p>Hi {{ first_name }}</p>",
        "body_text": "Hi there",
    }
    template_resp = client.post("/templates/", json=template_payload)
    template_id = template_resp.json()["id"]

    campaign_payload = {
        "name": "Launch",
        "account_id": account_id,
        "template_id": template_id,
        "schedule_type": "one_time",
        "schedule_config": {"run_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()},
        "target_tags": "news",
        "active": True,
    }
    campaign_resp = client.post("/campaigns/", json=campaign_payload)
    campaign_id = campaign_resp.json()["id"]

    client.post(
        "/contacts/",
        json={"email": "a@example.com", "name": "Alice Example", "tags": "news"},
    )
    client.post(
        "/contacts/",
        json={"email": "b@example.com", "name": "Bob Example", "tags": "news"},
    )

    run_campaigns()

    session = SessionLocal()
    try:
        queued = session.query(models.QueuedEmail).all()
        assert len(queued) == 2
        assert all(email.campaign_id == campaign_id for email in queued)
        assert all(email.account_id == account_id for email in queued)
    finally:
        session.close()
