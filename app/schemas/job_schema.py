import enum
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.job_model import JobStatus


class SalarySlabEnum(str, enum.Enum):
    BELOW_3LPA = "BELOW_3LPA"     # < ₹3,00,000 (Volume / Associate)
    FROM_3L_TO_10L = "3L_TO_10L"  # ₹3,00,000 - ₹10,00,000 (Mid / Senior)
    ABOVE_10LPA = "ABOVE_10LPA"   # > ₹10,00,000 (Leadership / Executive)


class ServiceTrackEnum(str, enum.Enum):
    CONTRACT_STAFFING = "Contract Staffing"
    TALENT_ACQUISITION = "Talent Acquisition"
    BULK_HIRING = "Bulk Hiring"
    LEADERSHIP_HIRING = "Leadership Hiring"


class JobCreate(BaseModel):
    company_id: str
    title: str = Field(..., min_length=3)
    service_track: Optional[ServiceTrackEnum] = ServiceTrackEnum.TALENT_ACQUISITION
    department: str
    location: str
    workplace_type: Optional[str] = "Onsite"
    employment_type: Optional[str] = "Full-time"
    experience_min: int = Field(default=0, ge=0)
    experience_max: int = Field(default=5, ge=0)
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    is_salary_hidden: bool = False
    description: str = Field(..., min_length=20)
    requirements: Optional[str] = None
    skills: List[str] = []


class JobUpdate(BaseModel):
    title: Optional[str] = None
    service_track: Optional[ServiceTrackEnum] = None
    department: Optional[str] = None
    location: Optional[str] = None
    workplace_type: Optional[str] = None
    employment_type: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    is_salary_hidden: Optional[bool] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    skills: Optional[List[str]] = None
    status: Optional[JobStatus] = None


class JobResponse(BaseModel):
    id: str
    company_id: str
    recruiter_id: Optional[str] = None
    title: str
    slug: str
    service_track: Optional[str] = None
    department: str
    location: str
    workplace_type: str
    employment_type: str
    experience_min: int
    experience_max: int
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    is_salary_hidden: bool
    description: str
    requirements: Optional[str] = None
    skills: List[str]
    status: JobStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobSearchFeedResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[JobResponse]