import uuid
from typing import Optional
from app.core.redis import redis_client

SESSION_EXPIRY_SECONDS = 86400 * 7  # 7 Days


class SessionService:
    @staticmethod
    async def create_user_session(
        user_id: str, 
        ip_address: Optional[str] = None, 
        user_agent: Optional[str] = None
    ) -> str:
        """
        Registers an active session ID in Redis for the user.
        Allows instant revocation upon logout or password reset.
        """
        session_id = str(uuid.uuid4())
        session_key = f"session:{user_id}:{session_id}"
        
        session_data = {
            "session_id": session_id,
            "ip": ip_address or "unknown",
            "device": (user_agent or "unknown")[:120],
        }
        
        await redis_client.hset(session_key, mapping=session_data)
        await redis_client.expire(session_key, SESSION_EXPIRY_SECONDS)
        await redis_client.sadd(f"user_sessions:{user_id}", session_id)
        return session_id

    @staticmethod
    async def is_session_active(user_id: str, session_id: str) -> bool:
        """Checks if a user session is active in Redis."""
        session_key = f"session:{user_id}:{session_id}"
        return bool(await redis_client.exists(session_key))

    @staticmethod
    async def terminate_session(user_id: str, session_id: str):
        """Terminates an individual session (single-device logout)."""
        await redis_client.delete(f"session:{user_id}:{session_id}")
        await redis_client.srem(f"user_sessions:{user_id}", session_id)

    @staticmethod
    async def terminate_all_user_sessions(user_id: str):
        """Terminates all active sessions (after password reset or security revocation)."""
        session_ids = await redis_client.smembers(f"user_sessions:{user_id}")
        if session_ids:
            keys_to_delete = [f"session:{user_id}:{sid}" for sid in session_ids]
            await redis_client.delete(*keys_to_delete)
        await redis_client.delete(f"user_sessions:{user_id}")