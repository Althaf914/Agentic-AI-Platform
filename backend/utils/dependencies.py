"""
FastAPI dependency injection utilities.
"""

from typing import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.database.session import SessionLocal
from backend.models.user import User
from backend.services.auth_service import decode_token
from backend.utils.exceptions import UnauthorizedError, ForbiddenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db():
    """Yields a SQLAlchemy session, closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decodes JWT and returns the authenticated User or raises 401."""
    payload = decode_token(token)
    if payload is None:
        raise UnauthorizedError()

    user_id: str = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError()

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedError(detail="User not found")

    return user


def require_role(roles: list[str]) -> Callable:
    """
    Dependency factory — checks that the current user has one of the allowed roles.
    Usage: Depends(require_role(["admin", "sales"]))
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError(
                detail=f"Role '{current_user.role}' is not allowed. Required: {roles}"
            )
        return current_user

    return role_checker
