from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_admin, require_recruiter_or_admin
from app.core.security import get_password_hash
from app.models.candidate_model import ApplicationStatus, CandidateProfile, JobApplication
from app.models.inquiries_model import Inquiry, InquiryStatus
from app.models.job_model import Job, JobStatus
from app.models.user_model import Company, User, UserRole
from app.schemas.admin_schema import (
    InquiriesMetric,
    JobsMetric,
    PipelineMetric,
    PlatformStatsResponse,
)
from app.schemas.user_schema import (
    ROLE_DEFAULT_PERMISSIONS,
    AdminUserCreate,
    AdminUserUpdate,
    UserResponse,
)

router = APIRouter()


# --------------------------------------------------------------------------
# 1. Platform Dashboard & Lead KPI Analytics
# --------------------------------------------------------------------------
@router.get("/dashboard-stats", response_model=PlatformStatsResponse)
def get_platform_dashboard_stats(
    current_user: User = Depends(require_recruiter_or_admin),
    db: Session = Depends(get_db),
):
    """
    Recruiter / Admin: Aggregated KPI metrics across inquiries,
    job listings, ATS pipeline, and candidate registrations.
    """
    total_candidates = db.query(CandidateProfile).count()
    total_companies = db.query(Company).count()

    # Inquiry Lead Metrics
    inquiry_rows = db.query(Inquiry.status, func.count(Inquiry.id)).group_by(Inquiry.status).all()
    inquiry_status_map = {status.value if hasattr(status, "value") else str(status): count for status, count in inquiry_rows}

    source_rows = db.query(Inquiry.source, func.count(Inquiry.id)).group_by(Inquiry.source).all()
    inquiry_source_map = {src.value if hasattr(src, "value") else str(src): count for src, count in source_rows}

    total_inquiries = sum(inquiry_status_map.values())
    inquiries_data = InquiriesMetric(
        total=total_inquiries,
        new=inquiry_status_map.get(InquiryStatus.NEW.value, 0),
        contacted=inquiry_status_map.get(InquiryStatus.CONTACTED.value, 0),
        converted=inquiry_status_map.get(InquiryStatus.CONVERTED.value, 0),
        by_source=inquiry_source_map,
    )

    # Job Metrics & Tracks
    job_rows = db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
    job_status_map = {status.value if hasattr(status, "value") else str(status): count for status, count in job_rows}

    track_rows = (
        db.query(Job.service_track, func.count(Job.id))
        .filter(Job.service_track.isnot(None))
        .group_by(Job.service_track)
        .all()
    )
    job_track_map = {str(track): count for track, count in track_rows}

    total_jobs = sum(job_status_map.values())
    jobs_data = JobsMetric(
        total=total_jobs,
        active=job_status_map.get(JobStatus.ACTIVE.value, 0),
        paused=job_status_map.get(JobStatus.PAUSED.value, 0),
        closed=job_status_map.get(JobStatus.CLOSED.value, 0),
        by_track=job_track_map,
    )

    # ATS Applicant Pipeline Stages
    app_rows = db.query(JobApplication.status, func.count(JobApplication.id)).group_by(JobApplication.status).all()
    app_status_map = {status.value if hasattr(status, "value") else str(status): count for status, count in app_rows}

    total_apps = sum(app_status_map.values())
    pipeline_data = PipelineMetric(
        total_applications=total_apps,
        applied=app_status_map.get(ApplicationStatus.APPLIED.value, 0),
        screening=app_status_map.get(ApplicationStatus.SCREENING.value, 0),
        shortlisted=app_status_map.get(ApplicationStatus.SHORTLISTED.value, 0),
        interview_scheduled=app_status_map.get(ApplicationStatus.INTERVIEW_SCHEDULED.value, 0),
        hired=app_status_map.get(ApplicationStatus.HIRED.value, 0),
        rejected=app_status_map.get(ApplicationStatus.REJECTED.value, 0),
    )

    return PlatformStatsResponse(
        candidates_count=total_candidates,
        companies_count=total_companies,
        inquiries=inquiries_data,
        jobs=jobs_data,
        pipeline=pipeline_data,
    )


# --------------------------------------------------------------------------
# 2. Super Admin User & Recruiter Management
# --------------------------------------------------------------------------
@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    payload: AdminUserCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: Provision a new user/recruiter account with specific roles and permissions."""
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="User with this email already exists")

    if payload.user_id:
        if db.query(User).filter(User.id == payload.user_id).first():
            raise HTTPException(status_code=400, detail="User ID already taken")

    assigned_perms = payload.permissions
    if assigned_perms is None:
        assigned_perms = ROLE_DEFAULT_PERMISSIONS.get(payload.role, [])

    new_user = User(
        id=payload.user_id if payload.user_id else None,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        permissions=assigned_perms,
        company_id=payload.company_id,
        is_active=payload.is_active,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("", response_model=List[UserResponse])
def admin_list_users(
    role: Optional[UserRole] = Query(None, description="Filter by User Role"),
    is_active: Optional[bool] = Query(None, description="Filter by Active Status"),
    skip: int = 0,
    limit: int = 50,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: Paginated list of registered users with role and status filtering."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    return query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserResponse)
def admin_get_user(
    user_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: View a specific user profile by user ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def admin_update_user(
    user_id: str,
    payload: AdminUserUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: Update user email, reset password, change role, or modify permissions."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == UserRole.SUPER_ADMIN and current_admin.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a Super Admin can alter a Super Admin account.",
        )

    if payload.email and payload.email != user.email:
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=400, detail="Email is already in use")
        user.email = payload.email

    if payload.password:
        user.hashed_password = get_password_hash(payload.password)

    if payload.role:
        user.role = payload.role
        if payload.permissions is None:
            user.permissions = ROLE_DEFAULT_PERMISSIONS.get(payload.role, [])

    if payload.permissions is not None:
        user.permissions = payload.permissions

    if payload.company_id is not None:
        user.company_id = payload.company_id

    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def admin_delete_user(
    user_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: Permanently delete a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Admins cannot delete their own active account")

    if user.role == UserRole.SUPER_ADMIN and current_admin.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super Admin cannot be deleted")

    db.delete(user)
    db.commit()
    return {"status": "success", "message": f"User {user_id} deleted successfully"}