import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from decimal import Decimal
from app.core.database import SessionLocal
from app.models.job_model import Job, JobStatus
from app.models.user_model import Company, User, UserRole

def seed_platform():
    db = SessionLocal()
    try:
        print("[*] Starting platform data seeding...")

        # 1. Fetch Super Admin or Recruiter
        admin_user = db.query(User).filter(User.role.in_([UserRole.SUPER_ADMIN, UserRole.ADMIN])).first()
        admin_id = admin_user.id if admin_user else None

        # 2. Seed Client Companies
        companies_data = [
            {
                "name": "Tata Consultancy Services",
                "slug": "tcs",
                "website": "https://www.tcs.com",
                "industry": "Information Technology",
                "company_size": "10,000+ employees",
                "is_verified": True,
            },
            {
                "name": "Reliance Retail Ltd",
                "slug": "reliance-retail",
                "website": "https://www.relianceretail.com",
                "industry": "Retail & Logistics",
                "company_size": "5,000+ employees",
                "is_verified": True,
            },
            {
                "name": "Paytm Financial Services",
                "slug": "paytm-fin",
                "website": "https://paytm.com",
                "industry": "Fintech & Banking",
                "company_size": "1,000 - 5,000 employees",
                "is_verified": True,
            },
        ]

        created_companies = {}
        for c in companies_data:
            existing = db.query(Company).filter(Company.slug == c["slug"]).first()
            if not existing:
                comp = Company(**c)
                db.add(comp)
                db.flush()
                created_companies[c["slug"]] = comp
                print(f" [+] Created Company: {c['name']}")
            else:
                created_companies[c["slug"]] = existing

        # 3. Seed Realistic Jobs Across 4 Disciplines & Salary Slabs
        jobs_data = [
            # 1. Contract Staffing (< 3LPA)
            {
                "company_slug": "reliance-retail",
                "title": "Warehouse Logistics Associate (Contract)",
                "slug": "warehouse-logistics-associate-contract-noida",
                "service_track": "Contract Staffing",
                "department": "Logistics & Supply Chain",
                "location": "Noida, Sector 63",
                "workplace_type": "Onsite",
                "employment_type": "Contract",
                "experience_min": 0,
                "experience_max": 2,
                "salary_min": Decimal("240000"),
                "salary_max": Decimal("280000"),
                "is_salary_hidden": False,
                "description": "Responsible for daily inward inventory handling, pick-and-pack fulfillment, dispatch manifests, and warehouse management system updates.",
                "requirements": "High school or Diploma holder. Basic computer knowledge. Ready for shift work.",
                "skills": ["Inventory", "Dispatch", "Logistics", "Warehouse Ops"],
                "status": JobStatus.ACTIVE,
            },
            # 2. Talent Acquisition (3L - 10L)
            {
                "company_slug": "tcs",
                "title": "Senior Talent Acquisition Specialist",
                "slug": "senior-talent-acquisition-specialist-delhi-ncr",
                "service_track": "Talent Acquisition",
                "department": "Human Resources",
                "location": "Gurugram, Cyber City",
                "workplace_type": "Hybrid",
                "employment_type": "Full-time",
                "experience_min": 3,
                "experience_max": 6,
                "salary_min": Decimal("600000"),
                "salary_max": Decimal("850000"),
                "is_salary_hidden": False,
                "description": "Leading full lifecycle recruitment for niche engineering and cloud infrastructure teams. Managing Boolean searches, screening rounds, and stakeholder interviews.",
                "requirements": "Bachelor's / MBA in HR. 3+ years in tech hiring. Solid understanding of ATS workflows.",
                "skills": ["Technical Sourcing", "ATS", "Screening", "LinkedIn Recruiter", "Offer Rollout"],
                "status": JobStatus.ACTIVE,
            },
            # 3. Bulk Hiring (< 3LPA)
            {
                "company_slug": "reliance-retail",
                "title": "Customer Support Representative (Volume Hiring)",
                "slug": "customer-support-representative-volume-hiring-delhi",
                "service_track": "Bulk Hiring",
                "department": "Customer Operations",
                "location": "Delhi NCR",
                "workplace_type": "Onsite",
                "employment_type": "Full-time",
                "experience_min": 0,
                "experience_max": 1,
                "salary_min": Decimal("220000"),
                "salary_max": Decimal("290000"),
                "is_salary_hidden": False,
                "description": "Handling incoming voice and chat queries for retail orders, deliveries, and payment settlements with high satisfaction scores.",
                "requirements": "Excellent verbal communication in English & Hindi. Freshers welcome.",
                "skills": ["Inbound Calling", "Customer Support", "CRM", "Email Writing"],
                "status": JobStatus.ACTIVE,
            },
            # 4. Leadership Hiring (> 10LPA)
            {
                "company_slug": "paytm-fin",
                "title": "Director of Engineering (Payments & Risk)",
                "slug": "director-of-engineering-payments-noida",
                "service_track": "Leadership Hiring",
                "department": "Engineering & Technology",
                "location": "Noida, Sector 98",
                "workplace_type": "Hybrid",
                "employment_type": "Full-time",
                "experience_min": 10,
                "experience_max": 16,
                "salary_min": Decimal("2800000"),
                "salary_max": Decimal("3800000"),
                "is_salary_hidden": False,
                "description": "Spearheading engineering strategy for high-throughput distributed payment settlement systems. Mentoring 4 engineering managers and 30+ engineers.",
                "requirements": "B.Tech/M.Tech in CS. Proven track record in high-scale distributed systems and microservices architecture.",
                "skills": ["System Design", "Microservices", "Distributed Systems", "Fintech", "Engineering Leadership"],
                "status": JobStatus.ACTIVE,
            },
        ]

        for j in jobs_data:
            existing_job = db.query(Job).filter(Job.slug == j["slug"]).first()
            if not existing_job:
                comp = created_companies[j["company_slug"]]
                new_job = Job(
                    company_id=comp.id,
                    recruiter_id=admin_id,
                    title=j["title"],
                    slug=j["slug"],
                    service_track=j["service_track"],
                    department=j["department"],
                    location=j["location"],
                    workplace_type=j["workplace_type"],
                    employment_type=j["employment_type"],
                    experience_min=j["experience_min"],
                    experience_max=j["experience_max"],
                    salary_min=j["salary_min"],
                    salary_max=j["salary_max"],
                    is_salary_hidden=j["is_salary_hidden"],
                    description=j["description"],
                    requirements=j["requirements"],
                    skills=j["skills"],
                    status=j["status"],
                )
                db.add(new_job)
                print(f" [+] Created Job Posting: {j['title']} ({j['service_track']})")

        db.commit()
        print("[✓] Platform data seeded successfully!")

    except Exception as exc:
        db.rollback()
        print(f"[!] Error seeding data: {exc}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_platform()