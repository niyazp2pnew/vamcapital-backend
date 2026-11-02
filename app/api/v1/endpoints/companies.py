import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_recruiter_or_admin
from app.models.user_model import Company, User
from app.schemas.user_schema import CompanyCreate, CompanyResponse, CompanyUpdate

router = APIRouter()


def slugify(text: str) -> str:
    return re.sub(r"[^\w\s-]", "", text.lower().strip()).replace(" ", "-")


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    current_user: User = Depends(require_recruiter_or_admin),
    db: Session = Depends(get_db),
):
    """Registers an employer/company record."""
    clean_slug = slugify(payload.name)
    if db.query(Company).filter(Company.slug == clean_slug).first():
        raise HTTPException(status_code=400, detail="Company name already registered")

    new_company = Company(
        name=payload.name,
        slug=clean_slug,
        website=payload.website,
        gstin=payload.gstin,
        industry=payload.industry,
        company_size=payload.company_size,
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company


@router.get("", response_model=List[CompanyResponse])
def list_companies(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Public/Employer: Browse registered enterprise companies."""
    return db.query(Company).order_by(Company.name.asc()).offset(skip).limit(limit).all()


@router.get("/{slug}", response_model=CompanyResponse)
def get_company_by_slug(slug: str, db: Session = Depends(get_db)):
    """Fetch company profile and verification details by slug."""
    company = db.query(Company).filter(Company.slug == slug).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.patch("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: str,
    payload: CompanyUpdate,
    current_user: User = Depends(require_recruiter_or_admin),
    db: Session = Depends(get_db),
):
    """Admin/Recruiter: Update company verification or corporate credentials."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, val)

    db.commit()
    db.refresh(company)
    return company