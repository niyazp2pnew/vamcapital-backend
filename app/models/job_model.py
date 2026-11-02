import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Numeric, Boolean, DateTime, ForeignKey, Enum, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class JobStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=gen_uuid)
    company_id = Column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    recruiter_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    service_track = Column(String, nullable=True, index=True)
    department = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False, index=True)
    workplace_type = Column(String, default="Onsite")
    employment_type = Column(String, default="Full-time")
    experience_min = Column(Integer, default=0, index=True)
    experience_max = Column(Integer, default=5)
    salary_min = Column(Numeric(12, 2), nullable=True)
    salary_max = Column(Numeric(12, 2), nullable=True, index=True)
    is_salary_hidden = Column(Boolean, default=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    skills = Column(ARRAY(String), default=[])
    status = Column(Enum(JobStatus), default=JobStatus.ACTIVE, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="jobs")
    recruiter = relationship("User", back_populates="jobs")
    applications = relationship("JobApplication", back_populates="job", cascade="all, delete-orphan")