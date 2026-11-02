import json
import re
from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_recruiter_or_admin
from app.core.redis import redis_client
from app.models.job_model import Job, JobStatus
from app.models.user_model import Company, User
from app.schemas.job_schema import (
    JobCreate,
    JobResponse,
    JobSearchFeedResponse,
    JobUpdate,
    SalarySlabEnum,
    ServiceTrackEnum,
)

router = APIRouter()

CACHE_PREFIX = "jobs:feed:*"
FEED_CACHE_TTL = 120  # 2 minutes cache validity for high throughput


def slugify(text: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", text.lower().strip())
    return re.sub(r"[\s_-]+", "-", clean)


async def purge_jobs_cache():
    """Scans and invalidates all cached job feeds in Redis."""
    try:
        keys = []
        async for key in redis_client.scan_iter("jobs:feed:*"):
            keys.append(key)
        if keys:
            await redis_client.delete(*keys)
    except Exception as exc:
        print(f"[Redis Cache Purge Error]: {exc}")


# --------------------------------------------------------------------------
# Public Faceted Job Discovery Feed
# --------------------------------------------------------------------------
@router.get("", response_model=JobSearchFeedResponse)
async def list_jobs(
    q: Optional[str] = Query(None, description="Keywords matching title, description, skills, or department"),
    location: Optional[str] = Query(None, description="Location/City (e.g. Noida, Delhi NCR, Gurugram)"),
    department: Optional[str] = Query(None, description="Department (e.g. IT, HR, Sales, Logistics)"),
    service_track: Optional[ServiceTrackEnum] = Query(None, description="VAM Recruitment Track"),
    salary_slab: Optional[SalarySlabEnum] = Query(None, description="Compensation tier (< ₹3L, ₹3L-₹10L, > ₹10L)"),
    min_exp: Optional[int] = Query(None, description="Filter jobs requiring at most this experience in years"),
    workplace_type: Optional[str] = Query(None, description="Onsite, Remote, or Hybrid"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db),
):
    """
    Naukri-Grade Search Feed:
    - Multi-keyword lookup across title, description, department, and skills
    - Salary tier filtering (Volume hiring vs. Mid/Senior search)
    - Service Track filtering
    - Caches query response in Redis for fast access
    """
    skip = (page - 1) * limit
    cache_key = (
        f"jobs:feed:{q}:{location}:{department}:{service_track}:"
        f"{salary_slab}:{min_exp}:{workplace_type}:{page}:{limit}"
    )

    try:
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
    except Exception:
        pass

    query = db.query(Job).filter(Job.status == JobStatus.ACTIVE)

    # 1. Multi-Field Text Matching
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(term),
                Job.description.ilike(term),
                Job.department.ilike(term),
                Job.skills.any(q.strip()),
            )
        )

    # 2. Location & Workplace Type
    if location:
        query = query.filter(Job.location.ilike(f"%{location.strip()}%"))
    if workplace_type:
        query = query.filter(Job.workplace_type.ilike(f"%{workplace_type.strip()}%"))

    # 3. Department & Service Track Filters
    if department:
        query = query.filter(Job.department.ilike(f"%{department.strip()}%"))
    if service_track:
        query = query.filter(Job.service_track == service_track.value)

    # 4. Experience Threshold
    if min_exp is not None:
        query = query.filter(Job.experience_min <= min_exp)

    # 5. Salary Slab Filtering
    if salary_slab == SalarySlabEnum.BELOW_3LPA:
        query = query.filter(Job.salary_max < Decimal("300000"))
    elif salary_slab == SalarySlabEnum.FROM_3L_TO_10L:
        query = query.filter(
            Job.salary_max >= Decimal("300000"),
            Job.salary_max <= Decimal("1000000")
        )
    elif salary_slab == SalarySlabEnum.ABOVE_10LPA:
        query = query.filter(Job.salary_max > Decimal("1000000"))

    total_count = query.count()
    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()

    response_payload = {
        "total": total_count,
        "page": page,
        "limit": limit,
        "items": [JobResponse.model_validate(j).model_dump(mode="json") for j in jobs],
    }

    try:
        await redis_client.setex(cache_key, FEED_CACHE_TTL, json.dumps(response_payload))
    except Exception:
        pass

    return response_payload


# --------------------------------------------------------------------------
# Public Single Job View
# --------------------------------------------------------------------------
@router.get("/{slug}", response_model=JobResponse)
def get_job_by_slug(slug: str, db: Session = Depends(get_db)):
    """Fetch individual job details for the public job description view."""
    job = db.query(Job).filter(Job.slug == slug).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    return job


# --------------------------------------------------------------------------
# Recruiter / Admin: Create, Edit & Archive Jobs
# --------------------------------------------------------------------------
@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def post_job(
    payload: JobCreate,
    current_user: User = Depends(require_recruiter_or_admin),
    db: Session = Depends(get_db),
):
    """
    Recruiter / Admin: Publish a new opening.
    Generates a unique SEO slug and purges the Redis cache.
    """
    company = db.query(Company).filter(Company.id == payload.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company does not exist")

    unique_slug = f"{slugify(payload.title)}-{slugify(payload.location)}-{int(datetime.utcnow().timestamp())}"

    data = payload.model_dump()
    if payload.service_track:
        data["service_track"] = payload.service_track.value

    new_job = Job(
        recruiter_id=current_user.id,
        slug=unique_slug,
        **data,
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # Invalidate cached searches so the new listing appears immediately
    await purge_jobs_cache()

    return new_job


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    payload: JobUpdate,
    current_user: User = Depends(require_recruiter_or_admin),
    db: Session = Depends(get_db),
):
    """
    Recruiter / Admin: Edit, pause, or close an existing job posting.
    Purges the Redis cache to reflect changes.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    update_dict = payload.model_dump(exclude_unset=True)
    if "service_track" in update_dict and update_dict["service_track"] is not None:
        update_dict["service_track"] = update_dict["service_track"].value

    for field, val in update_dict.items():
        setattr(job, field, val)

    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    await purge_jobs_cache()

    return job


@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
async def delete_job(
    job_id: str,
    current_user: User = Depends(require_recruiter_or_admin),
    db: Session = Depends(get_db),
):
    """
    Recruiter / Admin: Remove a job listing and evict cached entries.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(job)
    db.commit()

    await purge_jobs_cache()

    return {"status": "success", "message": f"Job {job_id} deleted successfully"}