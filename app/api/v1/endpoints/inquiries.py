from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_recruiter_or_admin
from app.models.inquiries_model import Inquiry, InquirySource, InquiryStatus
from app.models.user_model import User
from app.schemas.inquiry_schema import (
    CallbackRequestCreate,
    CandidateInquiryCreate,
    ContactMessageCreate,
    EnterpriseInquiryCreate,
    InquiryResponse,
    InquiryUpdatePanel,
)
from app.services.email_service import send_html_email

router = APIRouter()

NOTIFICATION_RECIPIENT = "contact@vamcapital.in"

# --------------------------------------------------------------------------
# Public Form Submissions with Resend Lead Alerts
# --------------------------------------------------------------------------

@router.post("/enterprise", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def submit_enterprise_inquiry(
    payload: EnterpriseInquiryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Form 1: Enterprise Staffing Inquiry (Hero Hire Talent / Payroll tab)"""
    inquiry = Inquiry(
        source=InquirySource.ENTERPRISE_STAFFING,
        full_name=payload.contact_person,
        company_name=payload.company_name,
        phone=payload.work_phone,
        solution_scope=payload.solution_scope,
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)

    # Dispatch email notification in background
    html_alert = f"""
    <h3>New Enterprise Staffing Inquiry</h3>
    <p><strong>Contact Person:</strong> {payload.contact_person}</p>
    <p><strong>Company:</strong> {payload.company_name}</p>
    <p><strong>Work Phone:</strong> {payload.work_phone}</p>
    <p><strong>Solution Scope:</strong> {payload.solution_scope}</p>
    """
    background_tasks.add_task(
        send_html_email,
        NOTIFICATION_RECIPIENT,
        f"🚨 Enterprise Lead: {payload.company_name}",
        html_alert
    )

    return inquiry


@router.post("/candidate", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def submit_candidate_inquiry(
    payload: CandidateInquiryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Form 2: Candidate Placement Desk (Hero Job Seeker tab)"""
    inquiry = Inquiry(
        source=InquirySource.CANDIDATE_PLACEMENT,
        full_name=payload.candidate_name,
        email=payload.email,
        phone=payload.phone,
        target_function=payload.target_function,
        experience_level=payload.experience_level,
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)

    html_alert = f"""
    <h3>New Candidate Placement Inquiry</h3>
    <p><strong>Name:</strong> {payload.candidate_name}</p>
    <p><strong>Email:</strong> {payload.email}</p>
    <p><strong>Phone:</strong> {payload.phone}</p>
    <p><strong>Target Function:</strong> {payload.target_function}</p>
    <p><strong>Experience:</strong> {payload.experience_level}</p>
    """
    background_tasks.add_task(
        send_html_email,
        NOTIFICATION_RECIPIENT,
        f"👤 Candidate Lead: {payload.candidate_name} ({payload.target_function})",
        html_alert
    )

    return inquiry


@router.post("/contact-message", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def submit_contact_message(
    payload: ContactMessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Form 3: Send a Message (Contact Us section)"""
    inquiry = Inquiry(
        source=InquirySource.CONTACT_MESSAGE,
        full_name=payload.name,
        company_name=payload.company_name,
        email=payload.email,
        phone=payload.phone,
        requirements=payload.requirements,
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)

    html_alert = f"""
    <h3>New Contact Message</h3>
    <p><strong>Name:</strong> {payload.name}</p>
    <p><strong>Company:</strong> {payload.company_name}</p>
    <p><strong>Email:</strong> {payload.email}</p>
    <p><strong>Phone:</strong> {payload.phone}</p>
    <p><strong>Requirements:</strong></p>
    <blockquote>{payload.requirements}</blockquote>
    """
    background_tasks.add_task(
        send_html_email,
        NOTIFICATION_RECIPIENT,
        f"✉️ Contact Message from {payload.name} ({payload.company_name})",
        html_alert
    )

    return inquiry


@router.post("/callback", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def submit_callback_request(
    payload: CallbackRequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Form 4: Request a Callback (Quick consultation modal)"""
    inquiry = Inquiry(
        source=InquirySource.CALLBACK_REQUEST,
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.official_email,
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)

    html_alert = f"""
    <h3>⚡ Immediate Callback Requested</h3>
    <p><strong>Name:</strong> {payload.full_name}</p>
    <p><strong>Phone:</strong> {payload.phone}</p>
    <p><strong>Official Email:</strong> {payload.official_email}</p>
    """
    background_tasks.add_task(
        send_html_email,
        NOTIFICATION_RECIPIENT,
        f"📞 Urgent Callback Request: {payload.full_name} ({payload.phone})",
        html_alert
    )

    return inquiry


# --------------------------------------------------------------------------
# Internal Recruiter / Admin Inquiry Panel
# --------------------------------------------------------------------------

@router.get("/panel", response_model=List[InquiryResponse])
def get_all_panel_inquiries(
    source: Optional[InquirySource] = Query(None, description="Filter by Form Source"),
    status: Optional[InquiryStatus] = Query(None, description="Filter by Lead Status"),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_recruiter_or_admin),
    db: Session = Depends(get_db),
):
    """Admin/Recruiter: Lists incoming leads across all 4 forms with status & source filtering."""
    query = db.query(Inquiry)
    if source:
        query = query.filter(Inquiry.source == source)
    if status:
        query = query.filter(Inquiry.status == status)

    return query.order_by(Inquiry.created_at.desc()).offset(skip).limit(limit).all()


@router.patch("/panel/{inquiry_id}", response_model=InquiryResponse)
def update_inquiry_by_admin(
    inquiry_id: str,
    payload: InquiryUpdatePanel,
    current_user: User = Depends(require_recruiter_or_admin),
    db: Session = Depends(get_db),
):
    """Admin/Recruiter: Update status (NEW -> CONTACTED -> CONVERTED), notes, or assigned staff."""
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry record not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(inquiry, field, val)

    inquiry.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(inquiry)
    return inquiry