import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger("fairsplit.email")

SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "false").lower() == "true"
EMAIL_FROM = os.environ.get("EMAIL_FROM", "FairSplit <noreply@localhost>")


def send_magic_link(email: str, link: str) -> None:
    """Deliver the magic-link email over SMTP.

    Defaults point at a local Mailpit instance (localhost:1025, no auth) for
    development — set SMTP_HOST/PORT/USER/PASSWORD/USE_TLS and EMAIL_FROM to
    point at a real provider (e.g. Resend's SMTP relay) in production.
    """
    message = EmailMessage()
    message["Subject"] = "Your FairSplit sign-in link"
    message["From"] = EMAIL_FROM
    message["To"] = email
    message.set_content(
        f"Sign in to FairSplit by following this link:\n\n{link}\n\n"
        "This link expires in 30 minutes."
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        if SMTP_USE_TLS:
            smtp.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(message)

    logger.info("Sent magic link to %s", email)
