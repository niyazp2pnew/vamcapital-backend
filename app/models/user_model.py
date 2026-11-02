import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    RECRUITER = "RECRUITER"
    EMPLOYER_ADMIN = "EMPLOYER_ADMIN"
    CANDIDATE = "CANDIDATE"


class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False, unique=True, index=True)
    slug = Column(String, nullable=False, unique=True, index=True)
    website = Column(String, nullable=True)
    gstin = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    company_size = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="company")
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CANDIDATE, nullable=False)
    permissions = Column(ARRAY(String), default=[])
    is_active = Column(Boolean, default=True)
    company_id = Column(String, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="users")
    candidate_profile = relationship("CandidateProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="recruiter")