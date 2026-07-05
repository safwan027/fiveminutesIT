
"""
mailer.py — Send the daily brief as a newsletter to hardcoded recipients
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import resend
from dotenv import load_dotenv
from pathlib import Path

BASE = Path(__file__).parent.parent
SUBSCRIBERS_PATH = BASE / "fiveminutesIT" / "data" / "subscribers.txt"

# RECIPIENTS = [
#     "safwannasar0@gmail.com"
# ]

RECIPIENTS = []

def _read_subscribers() -> list:
    if not SUBSCRIBERS_PATH.exists():
        print(f"  [Newsletter skipped] No subscribers file found at {SUBSCRIBERS_PATH}")
        return []
  
    with open(SUBSCRIBERS_PATH, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def send_newsletter(subject: str, html_content: str):
    """Send the newsletter to all hardcoded recipients."""
    load_dotenv()

    RECIPIENTS = _read_subscribers()
    print("RECIPIENTS",RECIPIENTS)

    if not RECIPIENTS:
        print("  [Newsletter skipped] No subscribers found.")
        return
        
    resend_key = os.getenv("RESEND_API_KEY")
    if resend_key:
        resend.api_key = resend_key
        _send_via_resend(subject, html_content)
    else:
        _send_via_smtp(subject, html_content)

def _send_via_resend(subject: str, html_content: str):
    success_count = 0
    print("RECIPIENTS",RECIPIENTS)
    for to_email in RECIPIENTS:
        try:
            resend.Emails.send(
                {
                    "from": "onboarding@resend.dev",
                    "to": to_email,
                    "subject": subject,
                    "html": html_content,
                }
            )
            success_count += 1
        except Exception as e:
            print(f"  Newsletter failed for {to_email} (Resend): {e}")
    print("success_count",success_count)
    if success_count > 0:
        print(f"  Newsletter sent to {success_count} subscribers via Resend")
    else:
        print(f"  Newsletter not sent to {success_count} subscribers via Resend")

def _send_via_smtp(subject: str, html_content: str):
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        print(f"  [Newsletter skipped — SMTP credentials not set]")
        return

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            
            success_count = 0
            for to_email in RECIPIENTS:
                try:
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"] = smtp_user
                    msg["To"] = to_email
                    
                    msg.attach(MIMEText(html_content, "html"))
                    
                    server.send_message(msg)
                    success_count += 1
                except Exception as e:
                    print(f"  Newsletter failed for {to_email} (SMTP): {e}")
                
        if success_count > 0:
            print(f"  Newsletter sent to {success_count} subscribers via SMTP")
    except Exception as e:
        print(f"  Newsletter failed (SMTP login/setup): {e}")
