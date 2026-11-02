from app.schemas.candidate_schema import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdateStatus,
    CandidateProfileCreate,
    CandidateProfileResponse,
    CandidateProfileUpdate,
)
from app.schemas.inquiry_schema import (
    CallbackRequestCreate,
    CandidateInquiryCreate,
    ContactMessageCreate,
    EnterpriseInquiryCreate,
    InquiryResponse,
    InquiryUpdatePanel,
)
from app.schemas.job_schema import (
    JobCreate,
    JobResponse,
    JobUpdate,
)
from app.schemas.user_schema import (
    AdminUserCreate,
    AdminUserUpdate,
    CandidateRegister,
    CompanyCreate,
    CompanyResponse,
    CompanyUpdate,
    ForgotPasswordRequest,
    ResendOTPRequest,
    ResetPasswordConfirm,
    ROLE_DEFAULT_PERMISSIONS,
    TokenResponse,
    UserLogin,
    UserResponse,
    VerifyActivationOTP,
)
# In app/schemas/__init__.py
from app.schemas.candidate_schema import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdateStatus,
    CandidateDossierResponse,
    CandidateProfileCreate,
    CandidateProfileResponse,
    CandidateProfileUpdate,
)
from app.schemas.admin_schema import PlatformStatsResponse

__all__ = [
    # Inquiries
    "EnterpriseInquiryCreate",
    "CandidateInquiryCreate",
    "ContactMessageCreate",
    "CallbackRequestCreate",
    "InquiryUpdatePanel",
    "InquiryResponse",
    # Users, Auth & OTP
    "ROLE_DEFAULT_PERMISSIONS",
    "UserLogin",
    "CandidateRegister",
    "VerifyActivationOTP",
    "ResendOTPRequest",
    "ForgotPasswordRequest",
    "ResetPasswordConfirm",
    "TokenResponse",
    "AdminUserCreate",
    "AdminUserUpdate",
    "UserResponse",
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    # Jobs
    "JobCreate",
    "JobUpdate",
    "JobResponse",
    # Candidates & Applications
    "CandidateProfileCreate",
    "CandidateProfileUpdate",
    "CandidateProfileResponse",
    "ApplicationCreate",
    "ApplicationUpdateStatus",
    "ApplicationResponse",
    "CandidateDossierResponse",
    #Admin Schema
    "PlatformStatsResponse",
]