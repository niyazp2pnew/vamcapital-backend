from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Safely extract database URI with fallback
db_uri = getattr(settings, "SQLALCHEMY_DATABASE_URI", None) or getattr(settings, "DATABASE_URL", None)

if not db_uri:
    raise ValueError("Neither SQLALCHEMY_DATABASE_URI nor DATABASE_URL is configured in settings.")

# Fix dialect prefix if copied directly as postgres:// from cloud providers
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_uri.startswith("postgresql://") and not db_uri.startswith("postgresql+psycopg2://"):
    db_uri = db_uri.replace("postgresql://", "postgresql+psycopg2://", 1)

# Enterprise Engine Configuration:
#postgresql://neondb_owner:npg_naLfCcX4s9Ek@ep-bitter-mountain-b5wqzrv8-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
# Neon Production Engine Configuration:
# - pool_size: 10 (leaner for serverless pooling)
# - max_overflow: 10
# - pool_timeout: 30
# - pool_recycle: 300 (5 minutes; cleanly drops connections before Neon suspends inactive compute)
# - pool_pre_ping: True (tests connection liveness before every checkout, crucial for waking up cold Neon instances)
engine = create_engine(
    db_uri,
    pool_size=10,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=300,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Guaranteed Session Lifecycle:
    Safely yields the DB session and always closes it in the finally block.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()