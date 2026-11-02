# app/schemas/candidate_schema.py
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.candidate_model import ApplicationStatus


# --- Structured Nested Career Entities ---
class ExperienceItem(BaseModel):
    company: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    location: Optional[str] = None
    start_date: str = Field(..., description="e.g. '2021-03'")
    end_date: Optional[str] = Field(None, description="e.g. '2024-01' or null if current")
    is_current: bool = False
    description: Optional[str] = None


class EducationItem(BaseModel):
    degree: str = Field(..., min_length=1)
    institution: str = Field(..., min_length=1)
    year_completed: Optional[str] = None
    grade_or_gpa: Optional[str] = None


class CertificationItem(BaseModel):
    name: str = Field(..., min_length=1)
    issuer: Optional[str] = None
    year: Optional[str] = None


# --- Candidate Profile Creation & Update ---
class CandidateProfileCreate(BaseModel):
    full_name: str = Field(..., min_length=2)
    headline: Optional[str] = Field(None, description="Professional headline / title summary")
    about: Optional[str] = Field(None, description="Executive bio / detailed about section")
    phone: str = Field(..., min_length=10)
    current_location: str
    preferred_locations: List[str] = []
    current_title: Optional[str] = None
    total_exp_months: int = Field(default=0, ge=0)
    current_ctc: Optional[Decimal] = None
    expected_ctc: Optional[Decimal] = None
    notice_period_days: int = Field(default=30, ge=0)
    skills: List[str] = []
    resume_url: Optional[str] = Field(None, description="Direct resume link (Google Drive, Dropbox, etc.)")
    linkedin_url: Optional[str] = Field(None, description="Candidate LinkedIn URL")
    portfolio_url: Optional[str] = Field(None, description="Portfolio or GitHub URL")
    experience_history: List[ExperienceItem] = []
    education_history: List[EducationItem] = []
    certifications: List[CertificationItem] = []


class CandidateProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    about: Optional[str] = None
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
    portfolio_url: Optional[str] = None
    experience_history: Optional[List[Dict[str, Any]]] = None
    education_history: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[Dict[str, Any]]] = None


class CandidateProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    headline: Optional[str] = None
    about: Optional[str] = None
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
    portfolio_url: Optional[str] = None
    experience_history: List[Dict[str, Any]] = []
    education_history: List[Dict[str, Any]] = []
    certifications: List[Dict[str, Any]] = []
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

    # Rich Candidate Dossier Fields
    candidate_id: str
    full_name: str
    headline: Optional[str] = None
    about: Optional[str] = None
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
    portfolio_url: Optional[str] = None
    experience_history: List[Dict[str, Any]] = []
    education_history: List[Dict[str, Any]] = []
    certifications: List[Dict[str, Any]] = []