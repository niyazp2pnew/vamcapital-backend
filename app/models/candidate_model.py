# app/models/candidate_model.py
import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Numeric, 
    DateTime, ForeignKey, Enum, ARRAY, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class ApplicationStatus(str, enum.Enum):
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    REJECTED = "REJECTED"
    HIRED = "HIRED"


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # 1. Identity & Core Overview
    full_name = Column(String, nullable=False)
    headline = Column(String, nullable=True)  # e.g., "Lead Talent Partner | 8+ Yrs BFSI & Tech Sourcing"
    about = Column(Text, nullable=True)        # Executive summary / professional bio
    phone = Column(String, unique=True, nullable=False)
    current_location = Column(String, nullable=False)
    preferred_locations = Column(ARRAY(String), default=[])
    
    # 2. Current Employment & CTC Metrics
    current_title = Column(String, nullable=True)
    total_exp_months = Column(Integer, default=0)
    current_ctc = Column(Numeric(10, 2), nullable=True)
    expected_ctc = Column(Numeric(10, 2), nullable=True)
    notice_period_days = Column(Integer, default=30)
    
    # 3. Core Competencies & Links
    skills = Column(ARRAY(String), default=[])
    resume_url = Column(String, nullable=True)      # Direct Google Drive / Dropbox link
    linkedin_url = Column(String, nullable=True)    # LinkedIn profile
    portfolio_url = Column(String, nullable=True)   # GitHub / Personal website / Dossier

    # 4. Rich Career History (Structured JSON)
    # List of: [{"company": "Vivo", "title": "Lead Recruiter", "start_date": "2021-03", "end_date": null, "is_current": true, "description": "..."}]
    experience_history = Column(JSON, default=list)

    # List of: [{"degree": "B.Tech Computer Science", "institution": "IIT Delhi", "year": "2019"}]
    education_history = Column(JSON, default=list)

    # List of: [{"name": "SHRM Certified Professional", "issuer": "SHRM", "year": "2022"}]
    certifications = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="candidate_profile")
    applications = relationship("JobApplication", back_populates="candidate", cascade="all, delete-orphan")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(String, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.APPLIED, index=True)
    recruiter_notes = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)
    stage_history = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="applications")
    candidate = relationship("CandidateProfile", back_populates="applications")