"""
test_newsletter.py — A quick script to test the email sending functionality
without having to run the entire data pipeline.
"""

from dotenv import load_dotenv
import os

# Load environment variables (like RESEND_API_KEY, SMTP credentials)
load_dotenv()

from newsletter import send_newsletter

def test_send():
    print("Starting newsletter test...")
    
    # 1. Check loaded credentials
    resend_key = os.getenv("RESEND_API_KEY")
    smtp_user = os.getenv("SMTP_USER")
    
    if resend_key:
        print("[OK] Found RESEND_API_KEY.")
    elif smtp_user:
        print("[OK] Found SMTP_USER.")
    else:
        print("[WARNING] No RESEND_API_KEY or SMTP_USER found in environment variables.")
        print("Please check your .env file.")
    
    # 2. Dummy HTML content for testing
    test_html = """
    <html>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1 style="color: #b20710;">5minIT Newsletter Test</h1>
            <p>If you are reading this email, your newsletter delivery system is working perfectly!</p>
            <p><strong>This is a test email sent from test_newsletter.py.</strong></p>
        </body>
    </html>
    """
    
    # 3. Call the send function
    subject = "[5minIT] Newsletter Configuration Test"
    print("\nTriggering send_newsletter()...")
    
    try:
        send_newsletter(subject, test_html)
        print("\n[SUCCESS] Test complete. Please check your inbox.")
    except Exception as e:
        print(f"\n[ERROR] Error during sending: {e}")

if __name__ == "__main__":
    test_send()
