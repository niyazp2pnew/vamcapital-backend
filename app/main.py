from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.init_db import init_db
from app.core.redis import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Verify DB connection & Seed Super Admin
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    yield
    # Shutdown: Close Redis connection pool
    try:
        await redis_client.close()
    except Exception:
        pass


app = FastAPI(
    title="VAM Capital Advisory API",
    description="Backend recruitment engine, ATS pipeline, and enterprise workforce portal.",
    version="1.0.0",
    lifespan=lifespan,
)

# Global Database Exception Boundary (Prevents Worker Crashes)
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    print(f"[SQLAlchemy Handled Error]: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred. Your transaction has been rolled back safely."},
    )


# Allowed Frontend Origins (Next.js Local Dev + Production)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://vamcapital.in",
    "https://www.vamcapital.in",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
        "service": "vam-backend",
        "database": "connected",
        "redis_cache": "connected" if redis_ok else "unavailable",
    }


# Mount API V1
app.include_router(api_router, prefix="/api/v1")