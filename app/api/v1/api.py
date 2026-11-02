from fastapi import APIRouter
from app.api.v1.endpoints import (
    admin_users,
    auth,
    candidates,
    companies,
    inquiries,
    jobs,
)

api_router = APIRouter()

# 1. Website Inquiries (4 Forms) & Lead Triage Panel
api_router.include_router(inquiries.router, prefix="/inquiries", tags=["Inquiries Engine"])

# 2. Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# 3. Super Admin User & Recruiter Management
api_router.include_router(admin_users.router, prefix="/admin/users", tags=["Admin User Management"])

# 4. Naukri-Style Companies / Employers
api_router.include_router(companies.router, prefix="/companies", tags=["Employer Companies"])

# 5. Naukri-Style Jobs Feed & Postings
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs Feed"])

# 6. Candidate Onboarding & ATS Applications
api_router.include_router(candidates.router, prefix="/candidates", tags=["Candidate & ATS Desk"])