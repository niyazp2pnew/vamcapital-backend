# app/api/v1/endpoints/candidates.py
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_recruiter_or_admin
from app.models.candidate_model import ApplicationStatus, CandidateProfile, JobApplication
from app.models.job_model import Job
from app.models.user_model import Company, User
from app.schemas.candidate_schema import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdateStatus,
    CandidateDossierResponse,
    CandidateProfileCreate,
    CandidateProfileResponse,
    CandidateProfileUpdate,
)
from app.services.email_service import (
    get_application_receipt_template,
    get_stage_update_template,
    send_html_email,
)

router = APIRouter()


# --------------------------------------------------------------------------
# Candidate Profile Management
# --------------------------------------------------------------------------

@router.get("/profile/me", response_model=CandidateProfileResponse)
def get_my_candidate_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Candidate: View own profile details.
    Auto-creates a default profile record if one does not exist yet.
    """
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        profile = CandidateProfile(
            user_id=current_user.id,
            full_name=current_user.email.split("@")[0].capitalize(),
            headline="",
            about="",
            phone=f"+91{current_user.id[:10]}",
            current_location="Delhi NCR",
            preferred_locations=["Noida", "Gurugram", "Delhi NCR"],
            total_exp_months=0,
            notice_period_days=30,
            skills=[],
            experience_history=[],
            education_history=[],
            certifications=[],
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return profile


@router.post("/profile", response_model=CandidateProfileResponse, status_code=status.HTTP_201_CREATED)
def create_or_upsert_profile(
    payload: CandidateProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Candidate: Upsert complete career credentials, bio, work history, and education."""
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    payload_data = payload.model_dump(exclude_unset=True)

    if profile:
        for field, value in payload_data.items():
            setattr(profile, field, value)
        profile.updated_at = datetime.utcnow()
    else:
        profile = CandidateProfile(user_id=current_user.id, **payload_data)
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile


@router.patch("/profile/me", response_model=CandidateProfileResponse)
def update_my_candidate_profile(
    payload: CandidateProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Candidate: Partially edit headline, bio, experience history, skills, or links."""
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        profile = CandidateProfile(
            user_id=current_user.id,
            full_name=current_user.email.split("@")[0].capitalize(),
            headline="",
            about="",
            phone=f"+91{current_user.id[:10]}",
            current_location="Delhi NCR",
            experience_history=[],
            education_history=[],
            certifications=[],
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    update_data = payload.model_dump(exclude_unset=True)

    if "phone" in update_data and update_data["phone"] != profile.phone:
        existing_phone = (
            db.query(CandidateProfile)
            .filter(
                CandidateProfile.phone == update_data["phone"],
                CandidateProfile.id != profile.id,
            )
            .first()
        )
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is already associated with another profile.",
            )

    for field, value in update_data.items():
        setattr(profile, field, value)

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/account", status_code=status.HTTP_200_OK)
def delete_my_candidate_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Candidate: Permanently deletes the logged-in candidate account and associated dossiers."""
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    if profile:
        db.query(JobApplication).filter(JobApplication.candidate_id == profile.id).delete()
        db.delete(profile)

    db.delete(current_user)
    db.commit()
    return {"status": "success", "message": "Candidate account and associated records deleted permanently."}


# --------------------------------------------------------------------------
# Candidate Job Applications
# --------------------------------------------------------------------------

@router.post("/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_to_job(
    payload: ApplicationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Candidate: 1-click application submission using complete profile dossier."""
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete your profile before applying.")

    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job requisition not found.")

    existing_app = (
        db.query(JobApplication)
        .filter(
            JobApplication.job_id == payload.job_id,
            JobApplication.candidate_id == profile.id,
        )
        .first()
    )
    if existing_app:
        raise HTTPException(status_code=400, detail="You have already applied to this role.")

    initial_stage = [{"stage": ApplicationStatus.APPLIED.value, "timestamp": datetime.utcnow().isoformat()}]

    application = JobApplication(
        job_id=payload.job_id,
        candidate_id=profile.id,
        status=ApplicationStatus.APPLIED,
        stage_history=initial_stage,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # Dispatch confirmation email via Resend
    company_name = job.company.name if job.company else "VAM Capital Client"
    receipt_html = get_application_receipt_template(
        candidate_name=profile.full_name,
        job_title=job.title,
        company_name=company_name,
    )
    background_tasks.add_task(
        send_html_email,
        current_user.email,
        f"Application Received: {job.title}",
        receipt_html,
    )

    return application


@router.get("/my-applications", response_model=List[ApplicationResponse])
def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Candidate: View tracking and status of all submitted applications."""
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        return []
    return (
        db.query(JobApplication)
        .filter(JobApplication.candidate_id == profile.id)
        .order_by(JobApplication.created_at.desc())
        .all()
    )


# --------------------------------------------------------------------------
# Recruiter ATS Desk & Dossier Management
# --------------------------------------------------------------------------

@router.get("/jobs/{job_id}/applicants", response_model=List[CandidateDossierResponse])
def list_job_applicants(
    job_id: str,
    status_filter: Optional[ApplicationStatus] = Query(None, description="Filter applicants by ATS status"),
    current_user: User = Depends(require_recruiter_or_admin),
    db: Session = Depends(get_db),
):
    """
    Recruiter ATS: Review all applicant dossiers for a job posting.
    Returns complete candidate information (headline, about, work history, education, CTC, resume link).
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    query = db.query(JobApplication).filter(JobApplication.job_id == job_id)
    if status_filter:
        query = query.filter(JobApplication.status == status_filter)

    applications = query.order_by(JobApplication.created_at.desc()).all()
    dossiers = []

    for app_item in applications:
        candidate = app_item.candidate
        user_record = candidate.user if candidate else None
        dossiers.append(
            CandidateDossierResponse(
                application_id=app_item.id,
                job_id=job.id,
                job_title=job.title,
                status=app_item.status,
                rating=app_item.rating,
                recruiter_notes=app_item.recruiter_notes,
                applied_at=app_item.created_at,
                stage_history=app_item.stage_history or [],
                candidate_id=candidate.id if candidate else "",
                full_name=candidate.full_name if candidate else "Unknown",
                headline=candidate.headline if candidate else None,
                about=candidate.about if candidate else None,
                email=user_record.email if user_record else "",
                phone=candidate.phone if candidate else "",
                current_location=candidate.current_location if candidate else "",
                current_title=candidate.current_title if candidate else None,
                total_exp_months=candidate.total_exp_months if candidate else 0,
                current_ctc=candidate.current_ctc if candidate else None,
                expected_ctc=candidate.expected_ctc if candidate else None,
                notice_period_days=candidate.notice_period_days if candidate else 30,
                skills=candidate.skills if candidate else [],
                resume_url=candidate.resume_url if candidate else None,
                linkedin_url=candidate.linkedin_url if candidate else None,
                portfolio_url=candidate.portfolio_url if candidate else None,
                experience_history=candidate.experience_history or [] if candidate else [],
                education_history=candidate.education_history or [] if candidate else [],
                certifications=candidate.certifications or [] if candidate else [],
            )
        )

    return dossiers


@router.patch("/applications/{application_id}/status", response_model=ApplicationResponse)
def update_application_stage(
    application_id: str,
    payload: ApplicationUpdateStatus,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_recruiter_or_admin),
    db: Session = Depends(get_db),
):
    """
    Recruiter ATS: Move applicant through hiring stages
    (APPLIED -> SCREENING -> SHORTLISTED -> INTERVIEW_SCHEDULED -> HIRED / REJECTED).
    """
    app_record = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application record not found")

    old_status = app_record.status
    history = app_record.stage_history or []
    history.append({
        "stage": payload.status.value,
        "updated_by": current_user.email,
        "timestamp": datetime.utcnow().isoformat(),
    })

    app_record.status = payload.status
    app_record.stage_history = history

    if payload.recruiter_notes:
        app_record.recruiter_notes = payload.recruiter_notes
    if payload.rating is not None:
        app_record.rating = payload.rating

    app_record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(app_record)

    # Dispatch status change email if status progressed
    if old_status != payload.status and app_record.candidate and app_record.candidate.user:
        candidate_email = app_record.candidate.user.email
        candidate_name = app_record.candidate.full_name
        job_title = app_record.job.title if app_record.job else "Position"

        status_email_html = get_stage_update_template(
            candidate_name=candidate_name,
            job_title=job_title,
            new_status=payload.status.value,
            notes=payload.recruiter_notes,
        )
        background_tasks.add_task(
            send_html_email,
            candidate_email,
            f"Update on Your Application for {job_title}",
            status_email_html,
        )

    return app_record

@router.get("/admin/applications", response_model=List[CandidateDossierResponse])
def list_all_applications_admin(
    status_filter: Optional[ApplicationStatus] = Query(None, description="Filter by stage"),
    job_id: Optional[str] = Query(None, description="Filter by specific job"),
    current_user: User = Depends(require_recruiter_or_admin),
    db: Session = Depends(get_db),
):
    """
    Admin/Recruiter: Master desk to monitor and triage all candidate applications.
    """
    query = db.query(JobApplication)
    if status_filter:
        query = query.filter(JobApplication.status == status_filter)
    if job_id:
        query = query.filter(JobApplication.job_id == job_id)

    applications = query.order_by(JobApplication.created_at.desc()).all()
    dossiers = []

    for app_item in applications:
        job = app_item.job
        candidate = app_item.candidate
        user_record = candidate.user if candidate else None
        
        dossiers.append(
            CandidateDossierResponse(
                application_id=app_item.id,
                job_id=job.id if job else "",
                job_title=job.title if job else "Archived Role",
                status=app_item.status,
                rating=app_item.rating,
                recruiter_notes=app_item.recruiter_notes,
                applied_at=app_item.created_at,
                stage_history=app_item.stage_history or [],
                candidate_id=candidate.id if candidate else "",
                full_name=candidate.full_name if candidate else "Unknown",
                headline=getattr(candidate, "headline", None),
                about=getattr(candidate, "about", None),
                email=user_record.email if user_record else "",
                phone=candidate.phone if candidate else "",
                current_location=candidate.current_location if candidate else "",
                current_title=getattr(candidate, "current_title", None),
                total_exp_months=candidate.total_exp_months if candidate else 0,
                current_ctc=candidate.current_ctc if candidate else None,
                expected_ctc=candidate.expected_ctc if candidate else None,
                notice_period_days=candidate.notice_period_days if candidate else 30,
                skills=candidate.skills if candidate else [],
                resume_url=candidate.resume_url if candidate else None,
                linkedin_url=candidate.linkedin_url if candidate else None,
                portfolio_url=getattr(candidate, "portfolio_url", None),
                experience_history=getattr(candidate, "experience_history", []) or [],
                education_history=getattr(candidate, "education_history", []) or [],
                certifications=getattr(candidate, "certifications", []) or [],
            )
        )

    return dossiers