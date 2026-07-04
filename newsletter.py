# """
# newsletter.py — Send the generated brief as an email newsletter to subscribers.
# """

# import os
# import urllib.request
# import smtplib
# from email.mime.text import MIMEText
# from pathlib import Path

# BASE = Path(__file__).parent.parent
# SUBSCRIBERS_PATH = BASE / "5minIT" / "data" / "subscribers.txt"

# def _read_subscribers() -> list:
#     if not SUBSCRIBERS_PATH.exists():
#         print(f"  [Newsletter skipped] No subscribers file found at {SUBSCRIBERS_PATH}")
#         return []
    
#     with open(SUBSCRIBERS_PATH, "r", encoding="utf-8") as f:
#         return [line.strip() for line in f if line.strip() and not line.startswith("#")]

# def send_newsletter(subject: str, html_content: str):
#     subscribers = _read_subscribers()
#     print(subscribers)
#     if not subscribers:
#         print("  [Newsletter skipped] No subscribers found.")
#         return

#     resend_key = os.getenv("RESEND_API_KEY")
#     print(resend_key)
#     if resend_key:
#         print(f"  Sending newsletter via Resend to {len(subscribers)} subscribers...")
#         _send_via_resend(resend_key, subscribers, subject, html_content)
#     else:
#         print(f"  Sending newsletter via SMTP to {len(subscribers)} subscribers...")
#         _send_via_smtp(subscribers, subject, html_content)

# def _send_via_resend(api_key: str, to_emails: list, subject: str, html_body: str):
#     import json
    
#     # Resend supports bcc or sending to an array of emails
#     # To keep it private, we can use BCC or send individual emails. 
#     # For simplicity, we send via 'bcc' here to avoid everyone seeing each other's emails.
#     try:
#         payload_dict = {
#             "from": "onboarding@resend.dev", # Resend's free tier default
#             "to": [to_emails[0]], # First email as 'to'
#             "subject": subject,
#             "html": html_body,   
#         }
#         if len(to_emails) > 1:
#             payload_dict["to"] = to_emails[1:]
            
#         payload = json.dumps(payload_dict).encode("utf-8")

#         req = urllib.request.Request(
#             "https://api.resend.com/emails",
#             data=payload,
#             headers={
#                 "Authorization": f"Bearer {api_key}",
#                 "Content-Type": "application/json",
#             },
#         )

#         with urllib.request.urlopen(req, timeout=15) as resp:
#             print(f"  [SUCCESS] Newsletter successfully sent via Resend.")
#     except Exception as e:
#         print(f"  [ERROR] Newsletter failed (Resend): {e}")

# def _send_via_smtp(to_emails: list, subject: str, html_body: str):
#     smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
#     smtp_port = int(os.environ.get("SMTP_PORT", "587"))
#     smtp_user = os.environ.get("SMTP_USER", "")
#     smtp_pass = os.environ.get("SMTP_PASS", "")

#     if not smtp_user or not smtp_pass:
#         print("  [Newsletter skipped] SMTP credentials not set.")
#         return

#     try:
#         msg = MIMEText(html_body, "html")
#         msg["Subject"] = subject
#         msg["From"] = smtp_user
#         msg["To"] = smtp_user # Send to self
#         # msg["Bcc"] is handled by passing to_emails to send_message or sendmail
        
#         with smtplib.SMTP(smtp_host, smtp_port) as server:
#             server.starttls()
#             server.login(smtp_user, smtp_pass)
#             server.sendmail(smtp_user, to_emails, msg.as_string())
#         print(f"  [SUCCESS] Newsletter successfully sent via SMTP to {len(to_emails)} subscribers.")
#     except Exception as e:
#         print(f"  [ERROR] Newsletter failed (SMTP): {e}")



"""
mailer.py — Send the daily brief as a newsletter to hardcoded recipients
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import resend
from dotenv import load_dotenv

# HARDCODED RECIPIENTS: Add your email addresses here
RECIPIENTS = [
    "safwannasar0@gmail.com"
]

def send_newsletter(subject: str, html_content: str):
    """Send the newsletter to all hardcoded recipients."""
    load_dotenv()
    if not RECIPIENTS:
        print("  [Newsletter skipped — No RECIPIENTS defined in mailer.py]")
        return
        
    resend_key = os.getenv("RESEND_API_KEY")
    if resend_key:
        resend.api_key = resend_key
        _send_via_resend(subject, html_content)
    else:
        _send_via_smtp(subject, html_content)

def _send_via_resend(subject: str, html_content: str):
    success_count = 0
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
    
    if success_count > 0:
        print(f"  Newsletter sent to {success_count} recipients via Resend")

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
            print(f"  Newsletter sent to {success_count} recipients via SMTP")
    except Exception as e:
        print(f"  Newsletter failed (SMTP login/setup): {e}")
