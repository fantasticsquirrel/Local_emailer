from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from protonmailer import scheduler
from protonmailer.models import Account, QueuedEmail


@patch("protonmailer.scheduler.send_email")
def test_process_queued_emails_sends_and_updates_status(mock_send_email, session):
    mock_send_email.return_value = (True, None)
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
    session.add(account)
    session.commit()
    session.refresh(account)

    now = datetime.now(timezone.utc)
    email = QueuedEmail(
        account_id=account.id,
        from_address=account.email_address,
        to_address="to@example.com",
        subject="Hello",
        body_html="<p>Hi</p>",
        body_text="Hi",
        scheduled_for=now - timedelta(minutes=1),
        status="queued",
    )
    session.add(email)
    session.commit()

    scheduler.process_queued_emails()

    updated = session.query(QueuedEmail).first()
    assert updated.status == "sent"
    assert updated.sent_at is not None
    mock_send_email.assert_called_once()


@patch("protonmailer.scheduler.send_email")
def test_process_queued_emails_marks_failures(mock_send_email, session):
    mock_send_email.return_value = (False, "some error")
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
    session.add(account)
    session.commit()
    session.refresh(account)

    now = datetime.now(timezone.utc)
    email = QueuedEmail(
        account_id=account.id,
        from_address=account.email_address,
        to_address="fail@example.com",
        subject="Hello",
        body_html="<p>Hi</p>",
        body_text="Hi",
        scheduled_for=now - timedelta(minutes=1),
        status="queued",
    )
    session.add(email)
    session.commit()

    scheduler.process_queued_emails()

    updated = session.query(QueuedEmail).first()
    assert updated.status == "failed"
    assert updated.last_error == "some error"
    mock_send_email.assert_called_once()


@patch("protonmailer.scheduler.send_email")
def test_process_queued_emails_ignores_future_scheduled(mock_send_email, session):
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
    session.add(account)
    session.commit()
    session.refresh(account)

    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    email = QueuedEmail(
        account_id=account.id,
        from_address=account.email_address,
        to_address="future@example.com",
        subject="Hello",
        body_html="<p>Hi</p>",
        body_text="Hi",
        scheduled_for=future_time,
        status="queued",
    )
    session.add(email)
    session.commit()

    scheduler.process_queued_emails()

    updated = session.query(QueuedEmail).first()
    assert updated.status == "queued"
    assert updated.sent_at is None
    mock_send_email.assert_not_called()
