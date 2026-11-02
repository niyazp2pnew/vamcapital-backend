from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.inquiries_model import InquirySource, InquiryStatus


# Form 1: Enterprise Staffing Inquiry (Hero Hire Talent / Payroll tab)
class EnterpriseInquiryCreate(BaseModel):
    contact_person: str = Field(..., min_length=2, description="Contact Person / Full Name")
    company_name: str = Field(..., min_length=2, description="Organization Name")
    work_phone: str = Field(..., min_length=10, description="Work phone with country code")
    solution_scope: str = Field(..., description="Selected engagement scope")


# Form 2: Candidate Placement Desk (Hero Job Seeker tab)
class CandidateInquiryCreate(BaseModel):
    candidate_name: str = Field(..., min_length=2, description="Candidate Full Name")
    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., min_length=10, description="Phone number")
    target_function: str = Field(..., description="Target function / industry")
    experience_level: str = Field(..., description="Experience bracket")


# Form 3: Send a Message (Contact section)
class ContactMessageCreate(BaseModel):
    name: str = Field(..., min_length=2, description="Your Name")
    company_name: str = Field(..., min_length=2, description="Organization / Enterprise")
    email: EmailStr = Field(..., description="Corporate or personal email")
    phone: str = Field(..., min_length=10, description="Contact phone")
    requirements: str = Field(..., min_length=5, description="Staffing or payroll requirements")


# Form 4: Request a Callback (Quick modal)
class CallbackRequestCreate(BaseModel):
    full_name: str = Field(..., min_length=2, description="Full Name")
    phone: str = Field(..., min_length=10, description="Phone Number")
    official_email: EmailStr = Field(..., description="Official Email")


# Admin Panel Update Schema
class InquiryUpdatePanel(BaseModel):
    status: Optional[InquiryStatus] = None
    assigned_recruiter: Optional[str] = None
    internal_notes: Optional[str] = None


# Unified Inquiry Response Schema
class InquiryResponse(BaseModel):
    id: str
    source: InquirySource
    status: InquiryStatus
    full_name: str
    phone: str
    email: Optional[str] = None
    company_name: Optional[str] = None
    solution_scope: Optional[str] = None
    target_function: Optional[str] = None
    experience_level: Optional[str] = None
    requirements: Optional[str] = None
    assigned_recruiter: Optional[str] = None
    internal_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True