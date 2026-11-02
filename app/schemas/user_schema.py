from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user_model import UserRole

# Default role permissions mapping
ROLE_DEFAULT_PERMISSIONS = {
    UserRole.SUPER_ADMIN: ["*"],
    UserRole.ADMIN: [
        "inquiries:read", "inquiries:write",
        "jobs:read", "jobs:write", "jobs:delete",
        "companies:read", "companies:write",
        "candidates:read", "candidates:write",
        "users:read", "users:write",
    ],
    UserRole.RECRUITER: [
        "inquiries:read", "inquiries:write",
        "jobs:read", "jobs:write",
        "candidates:read", "candidates:write",
        "applications:read", "applications:write",
    ],
    UserRole.EMPLOYER_ADMIN: [
        "jobs:read", "jobs:write",
        "applications:read", "applications:write",
    ],
    UserRole.CANDIDATE: [
        "jobs:read", "profile:manage", "applications:apply",
    ],
}


# --- Candidate Public Registration ---
class CandidateRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password minimum 6 characters")
    full_name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=10)
    current_location: str = Field(..., min_length=2)
    resume_url: Optional[str] = Field(None, description="External URL to CV/Resume (Google Drive, Dropbox, etc.)")
    linkedin_url: Optional[str] = Field(None, description="Candidate LinkedIn profile URL")


# --- OTP Verification & Password Reset Schemas ---
class VerifyActivationOTP(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit activation code")


class ResendOTPRequest(BaseModel):
    email: EmailStr
    purpose: str = Field(default="ACTIVATION", description="'ACTIVATION' or 'PASSWORD_RESET'")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit reset code")
    new_password: str = Field(..., min_length=6, description="New account password")


# --- Authentication Schemas ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: UserRole
    permissions: List[str]


# --- Admin User Management Schemas ---
class AdminUserCreate(BaseModel):
    user_id: Optional[str] = Field(None, description="Optional custom user ID; UUID generated if omitted")
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.RECRUITER
    permissions: Optional[List[str]] = None
    company_id: Optional[str] = None
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[UserRole] = None
    permissions: Optional[List[str]] = None
    company_id: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    permissions: List[str]
    is_active: bool
    company_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Company Schemas ---
class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=2)
    website: Optional[str] = None
    gstin: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None


class CompanyUpdate(BaseModel):
    website: Optional[str] = None
    gstin: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    is_verified: Optional[bool] = None


class CompanyResponse(BaseModel):
    id: str
    name: str
    slug: str
    website: Optional[str] = None
    gstin: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True