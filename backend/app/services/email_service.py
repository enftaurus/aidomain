"""
Email service — clean interface over Zoho SMTP.
Routers must never interact with SMTP directly.
"""
import asyncio
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger


def send_email(
    recipient: str,
    subject: str,
    html_body: str,
    attachments: Optional[List[str]] = None,
) -> bool:
    """
    Send an email via Zoho SMTP.
    attachments: list of absolute file paths to attach as PDFs.
    Returns True on success, False on failure (non-raising).
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured — email not sent.")
        return False

    try:
        msg = MIMEMultipart("mixed")
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = recipient
        msg["Subject"] = subject

        # HTML body
        msg.attach(MIMEText(html_body, "html"))

        # Attachments
        for path_str in (attachments or []):
            path = Path(path_str)
            if not path.exists():
                logger.warning(f"Attachment not found: {path_str}")
                continue
            part = MIMEBase("application", "octet-stream")
            with open(path, "rb") as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={path.name}",
            )
            msg.attach(part)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, recipient, msg.as_string())

        logger.info(f"Email sent to {recipient}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Email failed to {recipient}: {e}")
        return False


def send_alert_email_engineer(engineer_email: str, machine_code: str, pdf_path: str) -> bool:
    subject = f"MachSense Alert — {machine_code} — Engineer Report"
    body = f"<p>Please review the attached engineer report for machine <strong>{machine_code}</strong>.</p>"
    return send_email(engineer_email, subject, body, [pdf_path] if pdf_path else [])


def send_alert_email_admin(admin_email: str, machine_code: str, pdf_path: str) -> bool:
    subject = f"MachSense Machine Alert — {machine_code} — Admin Report"
    body = f"<p>Please review the attached admin report for machine <strong>{machine_code}</strong>.</p>"
    return send_email(admin_email, subject, body, [pdf_path] if pdf_path else [])


def send_maintenance_email(engineer_email: str, machine_code: str, scheduled_at: str, maintenance_type: str) -> bool:
    subject = f"MachSense Maintenance Scheduled — {machine_code}"
    body = f"""
    <p>Maintenance has been scheduled for machine <strong>{machine_code}</strong>.</p>
    <ul>
        <li><strong>Type:</strong> {maintenance_type}</li>
        <li><strong>Scheduled:</strong> {scheduled_at}</li>
    </ul>
    <p>Please review the maintenance panel for full details.</p>
    """
    return send_email(engineer_email, subject, body)


def send_shutdown_email(recipients: List[str], machine_code: str) -> None:
    subject = f"MachSense — Manual Shutdown Recorded — {machine_code}"
    body = f"<p>Machine <strong>{machine_code}</strong> has been manually shut down. An audit record has been created.</p>"
    for r in recipients:
        send_email(r, subject, body)
