from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user_model import User, UserRole
from app.services.session_service import SessionService

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decodes JWT bearer token, checks Redis active session, and injects user record."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        session_id: str = payload.get("sid")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Redis check: Ensure session hasn't been logged out or revoked
    if session_id:
        active = await SessionService.is_session_active(user_id, session_id)
        if not active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired or was terminated. Please sign in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return user


class RoleChecker:
    """Dependency factory checking if current user holds an authorized role."""
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {[r.value for r in self.allowed_roles]}",
            )
        return current_user


require_super_admin = RoleChecker([UserRole.SUPER_ADMIN])
require_admin = RoleChecker([UserRole.SUPER_ADMIN, UserRole.ADMIN])
require_recruiter_or_admin = RoleChecker([UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.RECRUITER])