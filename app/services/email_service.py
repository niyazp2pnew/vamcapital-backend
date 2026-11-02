import random
import resend
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.redis import redis_client

resend.api_key = settings.RESEND_API_KEY

OTP_EXPIRY_SECONDS = 600       # 10 minutes
COOLDOWN_SECONDS = 60          # 60 seconds resend cooldown


def generate_otp() -> str:
    """Generates a secure 6-digit numerical OTP."""
    return f"{random.randint(100000, 999999)}"


async def store_otp(email: str, purpose: str) -> str:
    """Stores OTP in Redis with a 10-minute TTL and enforces a 60-second cooldown."""
    cooldown_key = f"otp_cooldown:{purpose}:{email}"
    is_cooling_down = await redis_client.get(cooldown_key)
    if is_cooling_down:
        ttl = await redis_client.ttl(cooldown_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {ttl} seconds before requesting a new OTP.",
        )

    otp = generate_otp()
    otp_key = f"otp:{purpose}:{email}"

    await redis_client.setex(otp_key, OTP_EXPIRY_SECONDS, otp)
    await redis_client.setex(cooldown_key, COOLDOWN_SECONDS, "1")
    return otp


async def verify_otp_token(email: str, purpose: str, candidate_otp: str) -> bool:
    """Validates the OTP and consumes it upon success."""
    otp_key = f"otp:{purpose}:{email}"
    stored_otp = await redis_client.get(otp_key)

    if not stored_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired or was not requested. Please request a new one.",
        )

    if stored_otp.strip() != candidate_otp.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Please check and try again.",
        )

    await redis_client.delete(otp_key)
    return True


def send_html_email(to_email: str, subject: str, html_body: str):
    """Dispatches transactional email via Resend API."""
    if not settings.RESEND_API_KEY:
        print(f"\n[RESEND SIMULATION] To: {to_email} | Subject: {subject}\n{html_body}\n")
        return

    sender = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    params: resend.Emails.SendParams = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }

    try:
        response = resend.Emails.send(params)
        print(f"[Resend Success] Email sent to {to_email}. ID: {response.get('id')}")
    except Exception as exc:
        print(f"[Resend Error] Failed to send email to {to_email}: {str(exc)}")


def get_otp_template(headline: str, otp: str, message: str) -> str:
    """Branded VAM Capital Dark Navy & Gold OTP Email Template."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; background-color: #060E21; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding: 40px 10px;">
        <tr>
          <td align="center">
            <table width="540" cellpadding="0" cellspacing="0" style="background-color: #FDFCF9; border-radius: 16px; border: 1px solid #C5A869; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
              <tr>
                <td style="background-color: #0B1B3D; padding: 28px 32px; border-bottom: 2px solid #C5A869; text-align: left;">
                  <h1 style="margin: 0; font-size: 20px; font-weight: 700; color: #FFFFFF; letter-spacing: 0.5px;">
                    VAM <span style="color: #DFCA96;">CAPITAL</span>
                  </h1>
                  <p style="margin: 4px 0 0; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #94A3B8;">Workforce Advisory</p>
                </td>
              </tr>
              <tr>
                <td style="padding: 36px 32px; color: #1E293B; line-height: 1.6;">
                  <h2 style="margin: 0 0 14px; font-size: 18px; color: #0B1B3D;">{headline}</h2>
                  <p style="margin: 0 0 24px; font-size: 14px; color: #475569;">{message}</p>
                  
                  <div style="background-color: #0B1B3D; border-radius: 12px; padding: 18px; text-align: center; margin: 28px 0; border: 1px solid #C5A869;">
                    <span style="font-family: monospace; font-size: 32px; font-weight: 800; letter-spacing: 10px; color: #DFCA96;">
                      {otp}
                    </span>
                  </div>
                  
                  <p style="margin: 0; font-size: 12px; color: #64748B;">
                    This one-time passcode is valid for <strong>10 minutes</strong>. Never share this code with anyone.
                  </p>
                </td>
              </tr>
              <tr>
                <td style="background-color: #F1EFEA; padding: 16px 32px; text-align: center; border-top: 1px solid #E2D9C8; font-size: 11px; color: #64748B;">
                  © 2026 VAM Capital Advisors Pvt Ltd. All rights reserved.
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """


def get_application_receipt_template(candidate_name: str, job_title: str, company_name: str) -> str:
    """Branded VAM Capital Application Receipt Email."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; background-color: #060E21; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding: 40px 10px;">
        <tr>
          <td align="center">
            <table width="560" cellpadding="0" cellspacing="0" style="background-color: #FDFCF9; border-radius: 16px; border: 1px solid #C5A869; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
              <tr>
                <td style="background-color: #0B1B3D; padding: 26px 32px; border-bottom: 2px solid #C5A869;">
                  <h1 style="margin: 0; font-size: 20px; font-weight: 700; color: #FFFFFF;">
                    VAM <span style="color: #DFCA96;">CAPITAL</span>
                  </h1>
                  <p style="margin: 4px 0 0; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #94A3B8;">Candidate Career Portal</p>
                </td>
              </tr>
              <tr>
                <td style="padding: 34px 32px; color: #1E293B; line-height: 1.6;">
                  <h2 style="margin: 0 0 12px; font-size: 18px; color: #0B1B3D;">Application Received!</h2>
                  <p style="font-size: 14px; color: #475569; margin: 0 0 20px;">
                    Dear <strong>{candidate_name}</strong>, your application has been successfully submitted to our talent evaluation desk.
                  </p>
                  
                  <div style="background-color: #F0ECE1; border-left: 4px solid #C5A869; border-radius: 6px; padding: 16px 20px; margin: 20px 0;">
                    <p style="margin: 0 0 6px; font-size: 13px; color: #64748B;">POSITION APPLIED:</p>
                    <p style="margin: 0; font-size: 16px; font-weight: 700; color: #0B1B3D;">{job_title}</p>
                    <p style="margin: 4px 0 0; font-size: 13px; color: #8E7745; font-weight: 600;">{company_name}</p>
                  </div>
                  
                  <p style="font-size: 13px; color: #64748B; margin: 20px 0 0;">
                    Our executive search recruiters review submissions on a rolling basis. You will receive real-time email notifications as your profile advances through screening and interview stages.
                  </p>
                </td>
              </tr>
              <tr>
                <td style="background-color: #F1EFEA; padding: 16px 32px; text-align: center; border-top: 1px solid #E2D9C8; font-size: 11px; color: #64748B;">
                  © 2026 VAM Capital Advisors Pvt Ltd. All rights reserved.
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """


def get_stage_update_template(candidate_name: str, job_title: str, new_status: str, notes: str | None = None) -> str:
    """Branded VAM Capital Stage Update Email."""
    status_display = new_status.replace("_", " ").title()
    notes_html = f"""
    <div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px 16px; margin-top: 16px;">
      <p style="margin: 0; font-size: 12px; color: #64748B; font-weight: 600;">RECRUITER NOTE:</p>
      <p style="margin: 4px 0 0; font-size: 13px; color: #1E293B;">{notes}</p>
    </div>
    """ if notes else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; background-color: #060E21; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding: 40px 10px;">
        <tr>
          <td align="center">
            <table width="560" cellpadding="0" cellspacing="0" style="background-color: #FDFCF9; border-radius: 16px; border: 1px solid #C5A869; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
              <tr>
                <td style="background-color: #0B1B3D; padding: 26px 32px; border-bottom: 2px solid #C5A869;">
                  <h1 style="margin: 0; font-size: 20px; font-weight: 700; color: #FFFFFF;">
                    VAM <span style="color: #DFCA96;">CAPITAL</span>
                  </h1>
                  <p style="margin: 4px 0 0; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #94A3B8;">Application Status Notification</p>
                </td>
              </tr>
              <tr>
                <td style="padding: 34px 32px; color: #1E293B; line-height: 1.6;">
                  <h2 style="margin: 0 0 12px; font-size: 18px; color: #0B1B3D;">Update on Your Application</h2>
                  <p style="font-size: 14px; color: #475569; margin: 0 0 18px;">
                    Dear <strong>{candidate_name}</strong>, there is an update regarding your application for <strong>{job_title}</strong>.
                  </p>
                  
                  <div style="background-color: #0B1B3D; border-radius: 10px; padding: 18px; text-align: center; margin: 20px 0; border: 1px solid #C5A869;">
                    <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: #DFCA96; display: block; margin-bottom: 4px;">CURRENT STATUS</span>
                    <span style="font-size: 22px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.5px;">{status_display}</span>
                  </div>
                  
                  {notes_html}

                  <p style="font-size: 13px; color: #64748B; margin: 24px 0 0;">
                    Log in to your VAM Capital Candidate Portal anytime to view your stage progression and credentials.
                  </p>
                </td>
              </tr>
              <tr>
                <td style="background-color: #F1EFEA; padding: 16px 32px; text-align: center; border-top: 1px solid #E2D9C8; font-size: 11px; color: #64748B;">
                  © 2026 VAM Capital Advisors Pvt Ltd. All rights reserved.
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """