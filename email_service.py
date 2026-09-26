import smtplib
from email.message import EmailMessage
from config import settings

def send_email(to: str, attachment: bytes, filename: str):
    msg = EmailMessage()
    msg["Subject"] = "Ocular — Attendance Export"
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg.set_content("Attached is the latest attendance export for your organization.")

    msg.add_attachment(
        attachment,
        maintype="text",
        subtype="csv",
        filename=filename,
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)