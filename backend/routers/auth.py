"""
Authentication router — login and register endpoints.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from backend.services.auth_service import hash_password, verify_password, create_access_token
from backend.utils.dependencies import get_db, require_role
from backend.utils.exceptions import UnauthorizedError, ValidationError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise UnauthorizedError(detail="Invalid email or password")

    if not verify_password(request.password, user.password_hash):
        raise UnauthorizedError(detail="Invalid email or password")

    token = create_access_token(user_id=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        role=user.role,
        user_id=user.id,
    )


@router.post("/register", response_model=TokenResponse)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Register a new user (admin only)."""
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise ValidationError(detail="Email already registered")

    if request.role not in ("admin", "sales", "viewer"):
        raise ValidationError(detail="Invalid role. Must be admin, sales, or viewer")

    new_user = User(
        id=str(uuid.uuid4()),
        email=request.email,
        password_hash=hash_password(request.password),
        role=request.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(user_id=new_user.id, role=new_user.role)
    return TokenResponse(
        access_token=token,
        role=new_user.role,
        user_id=new_user.id,
    )
