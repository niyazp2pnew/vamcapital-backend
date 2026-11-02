import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum
from app.core.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class InquirySource(str, enum.Enum):
    ENTERPRISE_STAFFING = "ENTERPRISE_STAFFING"  # Form 1
    CANDIDATE_PLACEMENT = "CANDIDATE_PLACEMENT"  # Form 2
    CONTACT_MESSAGE     = "CONTACT_MESSAGE"      # Form 3
    CALLBACK_REQUEST    = "CALLBACK_REQUEST"     # Form 4

class InquiryStatus(str, enum.Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    IN_PROGRESS = "IN_PROGRESS"
    CONVERTED = "CONVERTED"
    ARCHIVED = "ARCHIVED"

class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(String, primary_key=True, default=gen_uuid)
    source = Column(Enum(InquirySource), nullable=False, index=True)
    status = Column(Enum(InquiryStatus), default=InquiryStatus.NEW, index=True)
    
    # Common Contact Info
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False, index=True)
    email = Column(String, nullable=True)
    
    # Enterprise Specific (Form 1 & 3)
    company_name = Column(String, nullable=True)
    solution_scope = Column(String, nullable=True) # Permanent Talent Acquisition, Third-Party Payroll, Turnkey / Bulk, CXO
    
    # Candidate Specific (Form 2)
    target_function = Column(String, nullable=True)
    experience_level = Column(String, nullable=True) # Fresher (0-1 yr), Mid (2-5 yrs), Senior (5-10 yrs), Leadership (10+ yrs)
    
    # Contact & Detailed Message (Form 3)
    requirements = Column(Text, nullable=True)
    
    # Internal Panel Operations
    assigned_recruiter = Column(String, nullable=True)
    internal_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)