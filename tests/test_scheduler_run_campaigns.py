from datetime import datetime, timezone

from protonmailer import scheduler
from protonmailer.models import Account, Campaign, Contact, QueuedEmail, Template


def _freeze_time(monkeypatch, fixed_now: datetime) -> None:
    class FixedDateTime(datetime):  # type: ignore[misc]
        @classmethod
        def now(cls, tz=None):  # noqa: D401, ANN001
            return fixed_now if tz else fixed_now.replace(tzinfo=None)

    monkeypatch.setattr(scheduler, "datetime", FixedDateTime)


def test_run_campaigns_daily_campaign_enqueues_emails(session, monkeypatch):
    fixed_now = datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc)
    _freeze_time(monkeypatch, fixed_now)

    account = Account(
        display_name="Sender",
        email_address="sender@example.com",
        smtp_host="smtp.example.com",
        smtp_port=465,
        smtp_username="user",
        smtp_password_encrypted="pass",
        use_ssl=True,
        use_tls=False,
    )
    template = Template(
        name="Welcome",
        subject="Hello {{ name }}",
        body_html="<p>Hi {{ name }}</p>",
        body_text="Hi {{ name }}",
    )
    contacts = [
        Contact(email="client@example.com", name="Client One", tags="clients"),
        Contact(email="lead@example.com", name="Lead", tags="leads"),
    ]
    campaign = Campaign(
        name="Daily",
        account=account,
        template=template,
        schedule_type="recurring",
        schedule_config={"freq": "daily", "hour": 9, "minute": 30},
        target_tags="clients",
        active=True,
    )

    session.add_all([account, template, campaign] + contacts)
    session.commit()

    scheduler.run_campaigns()

    queued = session.query(QueuedEmail).all()
    assert len(queued) == 1
    queued_email = queued[0]
    assert queued_email.to_address == "client@example.com"
    assert queued_email.campaign_id == campaign.id
    assert queued_email.account_id == account.id
    assert queued_email.status == "queued"
    session.refresh(campaign)
    assert campaign.last_run_at == fixed_now


def test_run_campaigns_one_time_campaign_only_runs_once(session, monkeypatch):
    fixed_now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    _freeze_time(monkeypatch, fixed_now)

    account = Account(
        display_name="Sender",
        email_address="sender@example.com",
        smtp_host="smtp.example.com",
        smtp_port=465,
        smtp_username="user",
        smtp_password_encrypted="pass",
        use_ssl=True,
        use_tls=False,
    )
    template = Template(
        name="Promo",
        subject="Sale",
        body_html="<p>Sale</p>",
        body_text="Sale",
    )
    contacts = [Contact(email="one@example.com", name="One", tags="clients")]
    campaign = Campaign(
        name="One Time",
        account=account,
        template=template,
        schedule_type="one_time",
        schedule_config={"run_at": fixed_now.isoformat()},
        target_tags="clients",
        active=True,
    )

    session.add_all([account, template, campaign] + contacts)
    session.commit()

    scheduler.run_campaigns()
    first_run_count = session.query(QueuedEmail).count()
    assert first_run_count == 1
    session.refresh(campaign)
    assert campaign.last_run_at == fixed_now

    scheduler.run_campaigns()
    second_run_count = session.query(QueuedEmail).count()
    assert second_run_count == 1
