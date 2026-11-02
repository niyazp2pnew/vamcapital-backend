# app/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import SessionLocal, Base, engine
from app.core.init_db import init_db
from app.core.redis import redis_client

# Explicitly import all database models so Base.metadata discovers them before create_all()
from app.models.user_model import User, Company
from app.models.inquiries_model import Inquiry
from app.models.job_model import Job
from app.models.candidate_model import CandidateProfile, JobApplication
from app.models.otp_model import OTPRecord

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Synchronize database schema and auto-create missing tables (including otp_records)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("[DB] Database tables verified and created successfully.")
    except Exception as exc:
        logger.error(f"[DB] Error creating/verifying tables: {exc}")

    # 2. Seed default Super Admin credentials
    try:
        db = SessionLocal()
        try:
            init_db(db)
        finally:
            db.close()
        logger.info("[DB] Master admin seed verification complete.")
    except Exception as exc:
        logger.error(f"[DB] Initial seed verification error: {exc}")

    yield

    # 3. Shutdown: Gracefully release Redis connection pool if active
    try:
        await redis_client.close()
    except Exception:
        pass


app = FastAPI(
    title=getattr(settings, "PROJECT_NAME", "VAM Capital Advisory API"),
    description="Enterprise recruitment platform, ATS pipeline, and workforce infrastructure engine.",
    version="1.0.0",
    lifespan=lifespan,
)

# Global Database Exception Boundary
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"[SQLAlchemy Handled Error]: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "A database error occurred. Your transaction was rolled back safely."
        },
    )


# CORS Configuration for Local Next.js, Vercel Previews, and Production Domains
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://vamcapital.in",
    "https://www.vamcapital.in",
    "https://vam-capital-web.vercel.app",
]

# Incorporate any custom origins defined in configuration/environment
config_origins = getattr(settings, "BACKEND_CORS_ORIGINS", [])
if isinstance(config_origins, list):
    for origin in config_origins:
        if origin not in allowed_origins:
            allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    redis_ok = False
    try:
        redis_ok = await redis_client.ping()
    except Exception:
        pass

    return {
        "status": "healthy",
        "service": "vamcapital-backend",
        "database": "connected",
        "storage": "postgresql-native",
        "redis_cache": "connected" if redis_ok else "unavailable (using PostgreSQL fallback)",
    }


# Mount API V1 routes
app.include_router(api_router, prefix=getattr(settings, "API_V1_STR", "/api/v1"))