from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.candidate_model import CandidateProfile
from app.models.user_model import User, UserRole
from app.schemas.user_schema import (
    CandidateRegister,
    ForgotPasswordRequest,
    ResendOTPRequest,
    ResetPasswordConfirm,
    TokenResponse,
    UserLogin,
    UserResponse,
    VerifyActivationOTP,
)
from app.services.email_service import (
    get_otp_template,
    send_html_email,
    store_otp,
    verify_otp_token,
)
from app.services.session_service import SessionService

router = APIRouter()
security_bearer = HTTPBearer()


# --------------------------------------------------------------------------
# 1. Candidate Registration
# --------------------------------------------------------------------------
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def candidate_register(
    payload: CandidateRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        if existing_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An active account with this email already exists. Please log in.",
            )
        else:
            otp = await store_otp(payload.email, "ACTIVATION")
            html = get_otp_template(
                headline="Activate Your VAM Capital Account",
                otp=otp,
                message="Your account is pending activation. Use the code below to complete your candidate registration.",
            )
            background_tasks.add_task(
                send_html_email, payload.email, "Activate Your VAM Capital Account", html
            )
            return {
                "status": "pending_activation",
                "message": "Account pending activation. A new OTP has been sent to your email.",
                "email": payload.email,
            }

    if db.query(CandidateProfile).filter(CandidateProfile.phone == payload.phone).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A candidate profile with this phone number already exists.",
        )

    new_user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=UserRole.CANDIDATE,
        permissions=["jobs:read", "profile:manage", "applications:apply"],
        is_active=False,
    )
    db.add(new_user)
    db.flush()

    new_profile = CandidateProfile(
        user_id=new_user.id,
        full_name=payload.full_name,
        phone=payload.phone,
        current_location=payload.current_location,
        resume_url=payload.resume_url,
        linkedin_url=payload.linkedin_url,
    )
    db.add(new_profile)
    db.commit()

    otp = await store_otp(payload.email, "ACTIVATION")
    html = get_otp_template(
        headline="Activate Your VAM Capital Account",
        otp=otp,
        message="Thank you for registering with VAM Capital. Use this code to verify your email and activate your account.",
    )
    background_tasks.add_task(
        send_html_email, payload.email, "Confirm Your VAM Capital Registration", html
    )

    return {
        "status": "pending_activation",
        "message": "Registration successful. Please verify the 6-digit OTP sent to your email.",
        "email": payload.email,
    }


# --------------------------------------------------------------------------
# 2. Confirm OTP & Activate Candidate Account
# --------------------------------------------------------------------------
@router.post("/verify-activation", response_model=TokenResponse)
async def verify_activation_otp(
    payload: VerifyActivationOTP,
    request: Request,
    db: Session = Depends(get_db),
):
    await verify_otp_token(payload.email, "ACTIVATION", payload.otp)

    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User record not found.")

    user.is_active = True
    db.commit()
    db.refresh(user)

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    session_id = await SessionService.create_user_session(user.id, client_ip, user_agent)

    token = create_access_token(subject=user.id, session_id=session_id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        permissions=user.permissions or [],
    )


# --------------------------------------------------------------------------
# 3. Standard Login with Session Creation
# --------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is pending activation. Please verify your OTP.",
        )

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    session_id = await SessionService.create_user_session(user.id, client_ip, user_agent)

    token = create_access_token(subject=user.id, session_id=session_id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        permissions=user.permissions or [],
    )


# --------------------------------------------------------------------------
# 4. Logout (Revoke Active Session in Redis)
# --------------------------------------------------------------------------
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
):
    """Terminates the current device session in Redis."""
    try:
        payload = jwt.decode(
            credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        session_id = payload.get("sid")
        if session_id:
            await SessionService.terminate_session(current_user.id, session_id)
    except Exception:
        pass

    return {"status": "success", "message": "Successfully logged out. Session revoked."}


# --------------------------------------------------------------------------
# 5. Forgot Password Request
# --------------------------------------------------------------------------
@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password_request(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        return {
            "status": "success",
            "message": "If the account exists, a password reset OTP has been sent.",
        }

    otp = await store_otp(payload.email, "PASSWORD_RESET")
    html = get_otp_template(
        headline="Password Reset Request",
        otp=otp,
        message="A request was received to reset the password for your VAM Capital account. Enter the 6-digit code below.",
    )
    background_tasks.add_task(
        send_html_email, payload.email, "VAM Capital - Password Reset Code", html
    )

    return {
        "status": "success",
        "message": "If the account exists, a password reset OTP has been sent.",
        "email": payload.email,
    }


# --------------------------------------------------------------------------
# 6. Reset Password with OTP & Terminate All Prior Sessions
# --------------------------------------------------------------------------
@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password_confirm(
    payload: ResetPasswordConfirm,
    db: Session = Depends(get_db),
):
    await verify_otp_token(payload.email, "PASSWORD_RESET", payload.otp)

    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User record not found.")

    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()

    # Revoke all existing sessions across all devices for security
    await SessionService.terminate_all_user_sessions(user.id)

    return {
        "status": "success",
        "message": "Password successfully updated. All prior sessions have been logged out.",
    }


# --------------------------------------------------------------------------
# 7. Resend OTP
# --------------------------------------------------------------------------
@router.post("/resend-otp", status_code=status.HTTP_200_OK)
async def resend_otp(
    payload: ResendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    purpose = payload.purpose.upper()
    if purpose not in ("ACTIVATION", "PASSWORD_RESET"):
        raise HTTPException(
            status_code=400,
            detail="Invalid purpose. Must be 'ACTIVATION' or 'PASSWORD_RESET'.",
        )

    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account registered under this email.")

    otp = await store_otp(payload.email, purpose)
    headline = "Account Activation Code" if purpose == "ACTIVATION" else "Password Reset Code"
    html = get_otp_template(
        headline=headline,
        otp=otp,
        message=f"Here is your requested 6-digit one-time passcode for {purpose.lower().replace('_', ' ')}.",
    )
    background_tasks.add_task(
        send_html_email, payload.email, f"VAM Capital - {headline}", html
    )

    return {
        "status": "success",
        "message": "A fresh OTP has been dispatched to your registered email.",
    }


# --------------------------------------------------------------------------
# 8. Authenticated User Profile
# --------------------------------------------------------------------------
@router.get("/me", response_model=UserResponse)
def get_current_authenticated_user(current_user: User = Depends(get_current_user)):
    return current_user