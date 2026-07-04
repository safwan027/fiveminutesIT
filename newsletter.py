"""
newsletter.py — Send the generated brief as an email newsletter to subscribers.
"""

import os
import urllib.request
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

BASE = Path(__file__).parent.parent
SUBSCRIBERS_PATH = BASE / "5minIT" / "data" / "subscribers.txt"

def _read_subscribers() -> list:
    if not SUBSCRIBERS_PATH.exists():
        print(f"  [Newsletter skipped] No subscribers file found at {SUBSCRIBERS_PATH}")
        return []
    
    with open(SUBSCRIBERS_PATH, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def send_newsletter(subject: str, html_content: str):
    subscribers = _read_subscribers()
    if not subscribers:
        print("  [Newsletter skipped] No subscribers found.")
        return

    resend_key = os.getenv("RESEND_API_KEY")
    if resend_key:
        print(f"  Sending newsletter via Resend to {len(subscribers)} subscribers...")
        _send_via_resend(resend_key, subscribers, subject, html_content)
    else:
        print(f"  Sending newsletter via SMTP to {len(subscribers)} subscribers...")
        _send_via_smtp(subscribers, subject, html_content)

def _send_via_resend(api_key: str, to_emails: list, subject: str, html_body: str):
    import json
    
    # Resend supports bcc or sending to an array of emails
    # To keep it private, we can use BCC or send individual emails. 
    # For simplicity, we send via 'bcc' here to avoid everyone seeing each other's emails.
    try:
        payload = json.dumps({
            "from": "newsletter@resend.dev", # Should be a verified domain in a real setup
            "to": [to_emails[0]], # First email as 'to'
            "bcc": to_emails[1:], # Rest as 'bcc'
            "subject": subject,
            "html": html_body,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"  ✓ Newsletter successfully sent via Resend.")
    except Exception as e:
        print(f"  ✗ Newsletter failed (Resend): {e}")

def _send_via_smtp(to_emails: list, subject: str, html_body: str):
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        print("  [Newsletter skipped] SMTP credentials not set.")
        return

    try:
        msg = MIMEText(html_body, "html")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = smtp_user # Send to self
        # msg["Bcc"] is handled by passing to_emails to send_message or sendmail
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_emails, msg.as_string())
        print(f"  ✓ Newsletter successfully sent via SMTP to {len(to_emails)} subscribers.")
    except Exception as e:
        print(f"  ✗ Newsletter failed (SMTP): {e}")

