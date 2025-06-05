
import os, smtplib
from email.message import EmailMessage
from pathlib import Path

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_application(job, cv_path: Path):
    msg = EmailMessage()
    msg["Subject"] = f"{job['title']} – application"
    msg["From"] = GMAIL_USER
    msg["To"] = job.get("apply_email") or "hiring@example.com"
    msg.set_content(f"Hi,\n\nPlease find my CV attached for {job['title']} at {job['company']}.\n\nBest regards")
    with open(cv_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="octet-stream", filename=cv_path.name)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)
