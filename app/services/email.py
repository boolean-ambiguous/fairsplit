import html
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

# Same tokens as frontend/src/theme.ts (light mode is the base; dark mode
# applies via `prefers-color-scheme`, which the mail clients that honor it —
# Apple/iOS Mail, Outlook.com, and others — pick up from the <style> block).
_LIGHT = {
    "bg": "#e4e7f5",
    "surface": "#f8f9fd",
    "ink": "#292b31",
    "muted": "#75798c",
    "accent": "#796cbf",
    "accent_ink": "#f8f9fd",
    "border": "rgba(41,43,49,0.14)",
}
_DARK = {
    "bg": "#161826",
    "surface": "#232532",
    "ink": "#e9e9ed",
    "muted": "#b2b6ca",
    "accent": "#9184d9",
    "accent_ink": "#161826",
    "border": "rgba(233,233,237,0.16)",
}
_FONT_STACK = "Inter, -apple-system, 'Segoe UI', sans-serif"


def _render_html(preheader: str, heading: str, paragraphs: list[str], cta_label: str, cta_url: str) -> str:
    """A single-card transactional email matching the web app's Nocturne
    design tokens (see frontend/src/theme.ts) — same wordmark treatment,
    accent color, and type scale, so a FairSplit email reads as the same
    product as the app it links back into."""
    heading = html.escape(heading)
    preheader = html.escape(preheader)
    cta_label = html.escape(cta_label)
    cta_url = html.escape(cta_url, quote=True)
    paragraphs_html = "".join(
        f'<p class="fs-muted" style="margin:0 0 16px; font-family:{_FONT_STACK}; '
        f'font-size:15px; line-height:1.6; color:{_LIGHT["muted"]};">{html.escape(p)}</p>'
        for p in paragraphs
    )
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="color-scheme" content="light dark" />
    <style>
      @media (prefers-color-scheme: dark) {{
        .fs-bg {{ background:{_DARK["bg"]} !important; }}
        .fs-surface {{ background:{_DARK["surface"]} !important; border-color:{_DARK["border"]} !important; }}
        .fs-ink {{ color:{_DARK["ink"]} !important; }}
        .fs-muted {{ color:{_DARK["muted"]} !important; }}
        .fs-button, .fs-button a {{ background:{_DARK["accent"]} !important; color:{_DARK["accent_ink"]} !important; }}
      }}
    </style>
  </head>
  <body style="margin:0; padding:0; background:{_LIGHT["bg"]};">
    <div style="display:none; max-height:0; overflow:hidden; opacity:0;">{preheader}</div>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" class="fs-bg" style="background:{_LIGHT["bg"]};">
      <tr>
        <td align="center" style="padding:40px 16px;">
          <table role="presentation" width="480" cellpadding="0" cellspacing="0" class="fs-surface" style="max-width:480px; width:100%; background:{_LIGHT["surface"]}; border:1px solid {_LIGHT["border"]}; border-radius:16px;">
            <tr>
              <td style="padding:36px 32px;">
                <div style="font-family:{_FONT_STACK}; font-size:12px; font-weight:600; letter-spacing:0.1em; text-transform:uppercase; color:{_LIGHT["accent"]};">FairSplit</div>
                <h1 class="fs-ink" style="margin:16px 0 12px; font-family:{_FONT_STACK}; font-size:22px; font-weight:500; letter-spacing:-0.02em; color:{_LIGHT["ink"]};">{heading}</h1>
                {paragraphs_html}
                <table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 4px;">
                  <tr>
                    <td class="fs-button" style="border-radius:10px; background:{_LIGHT["accent"]};">
                      <a href="{cta_url}" class="fs-button" style="display:inline-block; padding:12px 24px; font-family:{_FONT_STACK}; font-size:15px; font-weight:500; color:{_LIGHT["accent_ink"]}; text-decoration:none; border-radius:10px;">{cta_label}</a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
          <p class="fs-muted" style="margin:20px 0 0; font-family:{_FONT_STACK}; font-size:12px; color:{_LIGHT["muted"]};">If you didn't request this, you can safely ignore this email.</p>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def _deliver(to: str, subject: str, text_body: str, html_body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = EMAIL_FROM
    message["To"] = to
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

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
    text_body = (
        "Sign in to FairSplit by following this link:\n\n"
        f"{link}\n\n"
        "This link expires in 30 minutes."
    )
    html_body = _render_html(
        preheader="Your FairSplit sign-in link is ready.",
        heading="Sign in to FairSplit",
        paragraphs=[
            "Click the button below to sign in. No password needed.",
            "This link expires in 30 minutes.",
        ],
        cta_label="Sign in",
        cta_url=link,
    )
    _deliver(email, "Your FairSplit sign-in link", text_body, html_body)
    logger.info("Sent magic link to %s", email)


def send_invite_email(email: str, link: str, inviter_name: str, group_name: str) -> None:
    """Invite someone without a FairSplit account to join a group. The link
    is a ready-to-use magic link — following it signs them in directly and
    (via _link_invited_memberships) drops them straight into the group."""
    subject = f'{inviter_name} added you to "{group_name}" on FairSplit'
    text_body = (
        f'{inviter_name} added you to the group "{group_name}" on FairSplit, an easy '
        "way to split expenses with friends.\n\n"
        f"Follow this link to sign in and see the group:\n\n{link}\n\n"
        "This link expires in 30 minutes."
    )
    html_body = _render_html(
        preheader=f'{inviter_name} added you to "{group_name}" on FairSplit.',
        heading=f'{inviter_name} added you to "{group_name}"',
        paragraphs=[
            "FairSplit is an easy way to split expenses with friends.",
            "Follow the link below to sign in and see the group.",
            "This link expires in 30 minutes.",
        ],
        cta_label="View group",
        cta_url=link,
    )
    _deliver(email, subject, text_body, html_body)
    logger.info("Sent group invite to %s", email)
