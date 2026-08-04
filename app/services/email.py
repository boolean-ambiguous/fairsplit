import logging

logger = logging.getLogger("fairsplit.email")


def send_magic_link(email: str, link: str) -> None:
    """Deliver the magic-link email.

    No email provider is configured for this project — the link is logged
    instead. Swap this function's body for a real provider (Postmark, SES,
    Resend, ...) to send actual email; every caller already goes through
    this one seam.
    """
    logger.info("Magic link for %s: %s", email, link)
    print(f"\n[FairSplit] Magic link for {email}:\n  {link}\n")
