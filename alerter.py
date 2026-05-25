"""
alerter.py — Send email alerts when pipeline fails or sources go stale
Uses Resend API (free tier: 100 emails/day)
Falls back to SMTP if RESEND_API_KEY not set
"""

import json
import os
import smtplib
import urllib.request
from datetime import date, timedelta
from email.mime.text import MIMEText
import resend


def send_alert(subject: str, body: str):
    """Send an alert email. Tries Resend first, falls back to SMTP."""
    to_email = os.getenv("ALERT_EMAIL") 
    if not to_email:
        print(f"  [Alert skipped — ALERT_EMAIL not set]: {subject}")
        return

    resend_key = os.getenv("RESEND_API_KEY")
    if resend_key:
        _send_via_resend(resend_key, to_email, subject, body)
    else:
        _send_via_smtp(to_email, subject, body)


    resend.api_key = os.getenv("RESEND_API_KEY")


def _send_via_resend(api_key: str, to_email: str, subject: str, body: str):
    try:
        payload = resend.Emails.send(
            {
                "from": "onboarding@resend.dev",
                "to": [to_email],
                "subject": f"[IT Brief] {subject}",
                "html": body,
            }
        )

        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"  Alert sent via Resend: {subject}")
    except Exception as e:
        print(f"  Alert failed (Resend): {e}")


def _send_via_smtp(to_email: str, subject: str, body: str):
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        print(f"  [Alert skipped — SMTP credentials not set]: {subject}")
        return

    try:
        msg = MIMEText(body)
        msg["Subject"] = f"[IT Brief] {subject}"
        msg["From"] = smtp_user
        msg["To"] = to_email

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"  Alert sent via SMTP: {subject}")
    except Exception as e:
        print(f"  Alert failed (SMTP): {e}")


def check_stale_sources(store: dict) -> list:
    """Return list of sources not seen in 3+ days."""
    stale = []
    cutoff = (date.today() - timedelta(days=3)).isoformat()
    for source in store["config"]["sources"]:
        if not source["active"]:
            continue
        last_seen = store["source_last_seen"].get(source["name"])
        if not last_seen or last_seen < cutoff:
            stale.append(source["name"])
    return stale
