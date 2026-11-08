import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def mail_available():
    return bool(settings().smtp_host and settings().smtp_from)


def send_account_mail(address, purpose, token):
    config = settings()
    action = "verify-email" if purpose == "verify" else "reset-password"
    # Fragment avoids tokens entering reverse-proxy request logs and Referer URLs.
    url = f"{config.app_origin}/{action}#token={token}"
    message = EmailMessage()
    message["From"], message["To"] = config.smtp_from, address
    message["Subject"] = (
        "Verify your TalentLens email" if purpose == "verify" else "Reset your TalentLens password"
    )
    message.set_content(
        f"Open this link to {action.replace('-', ' ')}:\n\n{url}\n\nThis link expires in 30 minutes and can be used once. If you did not request it, ignore this email."
    )
    cls = smtplib.SMTP_SSL if config.smtp_security == "ssl" else smtplib.SMTP
    kwargs = {"context": ssl.create_default_context()} if config.smtp_security == "ssl" else {}
    with cls(config.smtp_host, config.smtp_port, timeout=15, **kwargs) as smtp:
        if config.smtp_security == "starttls":
            smtp.starttls(context=ssl.create_default_context())
        if config.smtp_username:
            smtp.login(config.smtp_username, config.smtp_password)
        smtp.send_message(message)


def deliver_safely(address, purpose, token):
    try:
        send_account_mail(address, purpose, token)
    except Exception as exc:
        # Never include SMTP response text, recipient, credentials or recovery URL.
        logger.error("account_mail_delivery_failed type=%s", type(exc).__name__)
