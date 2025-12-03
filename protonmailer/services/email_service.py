import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Tuple, Union

from protonmailer.models.account import Account

logger = logging.getLogger(__name__)


def _build_message(
    account: Account,
    to_addresses: List[str],
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> MIMEMultipart | MIMEText:
    if body_text:
        message = MIMEMultipart("alternative")
        message.attach(MIMEText(body_text, "plain"))
        message.attach(MIMEText(body_html, "html"))
    else:
        message = MIMEText(body_html, "html")

    message["From"] = account.email_address
    message["To"] = ", ".join(to_addresses)
    message["Subject"] = subject
    return message


def send_email(
    account: Account,
    to_addresses: list[str] | str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> Tuple[bool, str | None]:
    """
    Send an email using SMTP credentials stored on the Account.

    Returns a tuple of (success, error_message).
    """

    recipients: List[str] = (
        [to_addresses] if isinstance(to_addresses, str) else list(to_addresses)
    )

    logger.info(
        "Attempting to send email from %s via %s to %s with subject '%s'",
        account.email_address,
        account.smtp_host,
        recipients,
        subject,
    )

    message = _build_message(account, recipients, subject, body_html, body_text)

    try:
        if account.use_ssl:
            smtp_client: Union[smtplib.SMTP, smtplib.SMTP_SSL] = smtplib.SMTP_SSL(
                account.smtp_host, account.smtp_port
            )
        else:
            smtp_client = smtplib.SMTP(account.smtp_host, account.smtp_port)

        with smtp_client as server:
            if not account.use_ssl and account.use_tls:
                server.starttls()

            server.login(account.smtp_username, account.smtp_password_encrypted)
            server.sendmail(account.email_address, recipients, message.as_string())

        logger.info("Email sent successfully to %s", recipients)
        return True, None
    except Exception as exc:  # noqa: BLE001
        error_message = str(exc)
        logger.error("Failed to send email to %s: %s", recipients, error_message)
        return False, error_message
