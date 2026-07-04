import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import HTTPException, status

from app.config.config import settings
import logging

logger = logging.getLogger(__name__)

def send_invitation_email(to_email: str, org_name: str, token: str) -> None:
    """
    Sends an onboarding invitation email containing a secure link.
    If SMTP credentials are not configured, it logs and prints details for local development.
    """
    invite_link = f"{settings.BASE_URL}/api/v1/auth/complete-setup?token={token}"
    subject = f"Invitation to join {org_name} on FocusGuard AI"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
                <h2 style="color: #2F4F4F;">Welcome to FocusGuard AI!</h2>
                <p>Hello,</p>
                <p>You have been invited to join <strong>{org_name}</strong> as an employee on the FocusGuard AI platform.</p>
                <p>Please click the button below to complete your account setup and join your organization:</p>
                <div style="margin: 30px 0; text-align: center;">
                    <a href="{invite_link}" style="background-color: #20B2AA; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">Set Up Account</a>
                </div>
                <p>If the button above does not work, please copy and paste the following URL into your web browser:</p>
                <p style="word-break: break-all; color: #008B8B;">{invite_link}</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;" />
                <p style="font-size: 0.8em; color: #777;">This invitation is time-sensitive and secure. If you were not expecting this invite, you can safely ignore this email.</p>
            </div>
        </body>
    </html>
    """

    # Local development mode fallback:
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("SMTP configuration is incomplete. Falling back to local console email output.")
        print("\n" + "="*80)
        print("DEVELOPMENT MOCK EMAIL INVITATION SENT")
        print(f"Recipient: {to_email}")
        print(f"Subject:   {subject}")
        print(f"Link:      {invite_link}")
        print("="*80 + "\n")
        return

    # Standard SMTP sending
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_PORT == 587:
                server.starttls()
            if settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
        logger.info(f"Successfully sent invitation email to {to_email}")
    except Exception as e:
        # Log detailed error for debugging
        logger.error(f"Failed to send email via SMTP to {to_email}: {e}", exc_info=True)
        # Return generic error to client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email delivery failed. Please verify SMTP settings or try again later."
        )
