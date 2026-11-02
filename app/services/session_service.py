# app/services/session_service.py
import uuid
from typing import Optional


class SessionService:
    @staticmethod
    async def create_user_session(user_id: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> str:
        """Returns a unique session ID embedded inside the JWT token."""
        return str(uuid.uuid4())

    @staticmethod
    async def is_session_active(user_id: str, session_id: str) -> bool:
        """Stateless: JWT signature and database is_active check handle validity."""
        return True

    @staticmethod
    async def terminate_session(user_id: str, session_id: str):
        pass

    @staticmethod
    async def terminate_all_user_sessions(user_id: str):
        pass