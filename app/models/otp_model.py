# app/models/otp_model.py
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from app.core.database import Base


class OTPRecord(Base):
    __tablename__ = "otp_records"

    id = Column(String, primary_key=True)  # Format: "PURPOSE:email"
    email = Column(String, index=True, nullable=False)
    purpose = Column(String, nullable=False)  # "ACTIVATION" or "PASSWORD_RESET"
    otp_code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_sent_at = Column(DateTime, default=datetime.utcnow)
    is_used = Column(Boolean, default=False)