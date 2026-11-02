from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.candidate_model import ApplicationStatus


# --- Candidate Profile Schemas ---
class CandidateProfileCreate(BaseModel):
    full_name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=10)
    current_location: str
    preferred_locations: List[str] = []
    current_title: Optional[str] = None
    total_exp_months: int = Field(default=0, ge=0)
    current_ctc: Optional[Decimal] = None
    expected_ctc: Optional[Decimal] = None
    notice_period_days: int = Field(default=30, ge=0)
    skills: List[str] = []
    resume_url: Optional[str] = Field(None, description="External resume link (Google Drive, Dropbox, etc.)")
    linkedin_url: Optional[str] = Field(None, description="Candidate LinkedIn profile URL")


class CandidateProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    current_location: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    current_title: Optional[str] = None
    total_exp_months: Optional[int] = None
    current_ctc: Optional[Decimal] = None
    expected_ctc: Optional[Decimal] = None
    notice_period_days: Optional[int] = None
    skills: Optional[List[str]] = None
    resume_url: Optional[str] = None
    linkedin_url: Optional[str] = None


class CandidateProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    phone: str
    current_location: str
    preferred_locations: List[str]
    current_title: Optional[str] = None
    total_exp_months: int
    current_ctc: Optional[Decimal] = None
    expected_ctc: Optional[Decimal] = None
    notice_period_days: int
    skills: List[str]
    resume_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- ATS Job Applications Schemas ---
class ApplicationCreate(BaseModel):
    job_id: str


class ApplicationUpdateStatus(BaseModel):
    status: ApplicationStatus
    recruiter_notes: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    candidate_id: str
    status: ApplicationStatus
    recruiter_notes: Optional[str] = None
    rating: Optional[int] = None
    stage_history: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Recruiter Candidate Dossier Schema ---
class CandidateDossierResponse(BaseModel):
    application_id: str
    job_id: str
    job_title: str
    status: ApplicationStatus
    rating: Optional[int] = None
    recruiter_notes: Optional[str] = None
    applied_at: datetime
    stage_history: List[Dict[str, Any]] = []

    # Candidate Profile fields
    candidate_id: str
    full_name: str
    email: str
    phone: str
    current_location: str
    current_title: Optional[str] = None
    total_exp_months: int
    current_ctc: Optional[Decimal] = None
    expected_ctc: Optional[Decimal] = None
    notice_period_days: int
    skills: List[str]
    resume_url: Optional[str] = None
    linkedin_url: Optional[str] = None