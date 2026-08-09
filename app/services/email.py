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


def _deliver(to: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = EMAIL_FROM
    message["To"] = to
    message.set_content(body)

    # Port 465 is implicit TLS (encrypted from the first byte) and needs
    # SMTP_SSL; STARTTLS (port 587, or plain/unencrypted for local Mailpit)
    # negotiates encryption after connecting in plaintext. Mixing the two up
    # (e.g. STARTTLS against port 465) fails before the server ever sees a
    # real request.
    smtp_cls = smtplib.SMTP_SSL if SMTP_PORT == 465 else smtplib.SMTP
    with smtp_cls(SMTP_HOST, SMTP_PORT) as smtp:
        if SMTP_USE_TLS and SMTP_PORT != 465:
            smtp.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(message)


def send_magic_link(email: str, link: str) -> None:
    """Deliver the magic-link email over SMTP.

    Defaults point at a local Mailpit instance (localhost:1025, no auth) for
    development — set SMTP_HOST/PORT/USER/PASSWORD/USE_TLS and EMAIL_FROM to
    point at a real provider (e.g. Resend's SMTP relay) in production.
    """
    _deliver(
        email,
        "Your FairSplit sign-in link",
        f"Sign in to FairSplit by following this link:\n\n{link}\n\n"
        "This link expires in 30 minutes.",
    )
    logger.info("Sent magic link to %s", email)


def send_invite_email(email: str, link: str, inviter_name: str, group_name: str) -> None:
    """Invite someone without a FairSplit account to join a group. The link
    is a ready-to-use magic link — following it signs them in directly and
    (via _link_invited_memberships) drops them straight into the group."""
    _deliver(
        email,
        f'{inviter_name} added you to "{group_name}" on FairSplit',
        f'{inviter_name} added you to the group "{group_name}" on FairSplit, an easy '
        "way to split expenses with friends.\n\n"
        f"Follow this link to sign in and see the group:\n\n{link}\n\n"
        "This link expires in 30 minutes.",
    )
    logger.info("Sent group invite to %s", email)
