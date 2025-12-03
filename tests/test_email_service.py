from unittest.mock import MagicMock, patch

from protonmailer.models.account import Account
from protonmailer.services.email_service import send_email


def make_account(**overrides: object) -> Account:
    defaults = {
        "display_name": "Test Account",
        "email_address": "from@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 465,
        "smtp_username": "user",
        "smtp_password_encrypted": "password",
        "use_ssl": True,
        "use_tls": False,
    }
    defaults.update(overrides)
    return Account(**defaults)


@patch("protonmailer.services.email_service.smtplib.SMTP_SSL")
def test_send_email_success_with_ssl(mock_smtp_ssl: MagicMock) -> None:
    account = make_account()
    smtp_context = MagicMock()
    mock_smtp_ssl.return_value.__enter__.return_value = smtp_context

    success, error = send_email(
        account, ["to@example.com"], "Hello", "<p>Hi</p>", "Hi"
    )

    assert success is True
    assert error is None
    mock_smtp_ssl.assert_called_once_with(account.smtp_host, account.smtp_port)
    smtp_context.login.assert_called_once_with(
        account.smtp_username, account.smtp_password_encrypted
    )
    smtp_context.sendmail.assert_called_once()


@patch("protonmailer.services.email_service.smtplib.SMTP")
def test_send_email_success_with_tls(mock_smtp: MagicMock) -> None:
    account = make_account(use_ssl=False, use_tls=True, smtp_port=587)
    smtp_context = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_context

    success, _ = send_email(account, ["tls@example.com"], "TLS", "<p>Hi</p>")

    assert success is True
    mock_smtp.assert_called_once_with(account.smtp_host, account.smtp_port)
    smtp_context.starttls.assert_called_once()
    login_call = smtp_context.login.call_count == 1
    assert login_call
    starttls_call_index = [call[0] for call in smtp_context.method_calls].index(
        ("starttls", (), {})
    )
    login_call_index = [call[0] for call in smtp_context.method_calls].index(
        ("login", (), {})
    )
    assert starttls_call_index < login_call_index


@patch("protonmailer.services.email_service.smtplib.SMTP")
def test_send_email_single_string_recipient(mock_smtp: MagicMock) -> None:
    account = make_account(use_ssl=False, use_tls=False)
    smtp_context = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_context

    send_email(account, "solo@example.com", "Single", "<p>Hi</p>")

    smtp_context.sendmail.assert_called_once()
    args, _ = smtp_context.sendmail.call_args
    assert args[0] == account.email_address
    assert args[1] == ["solo@example.com"]


@patch("protonmailer.services.email_service.smtplib.SMTP_SSL")
def test_send_email_failure_raises_error(mock_smtp_ssl: MagicMock) -> None:
    account = make_account()
    smtp_context = MagicMock()
    smtp_context.sendmail.side_effect = RuntimeError("boom")
    mock_smtp_ssl.return_value.__enter__.return_value = smtp_context

    success, error = send_email(
        account, ["fail@example.com"], "Oops", "<p>Hi</p>", "Hi"
    )

    assert success is False
    assert error is not None
    assert "boom" in error
