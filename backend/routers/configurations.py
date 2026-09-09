"""
Configuration router — CRUD for ICP, Persona, and Scoring configs.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.configuration import Configuration
from backend.schemas.configuration import (
    ConfigSaveRequest,
    ConfigListResponse,
    ConfigDetailResponse,
)
from backend.utils.dependencies import get_db, get_current_user
from backend.utils.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/config", tags=["Configurations"])


def _save_config(config_type: str, request: ConfigSaveRequest, user: User, db: Session) -> Configuration:
    """Helper to save a configuration of a specific type."""
    if request.type != config_type:
        raise ValidationError(detail=f"Expected type '{config_type}', got '{request.type}'")

    config = Configuration(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name=request.name,
        type=request.type,
        config_json=request.config_json,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.post("/icp", response_model=ConfigDetailResponse)
def save_icp(
    request: ConfigSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save an ICP configuration."""
    request.type = "icp"
    config = _save_config("icp", request, current_user, db)
    return config


@router.post("/persona", response_model=ConfigDetailResponse)
def save_persona(
    request: ConfigSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save a Persona configuration."""
    request.type = "persona"
    config = _save_config("persona", request, current_user, db)
    return config


@router.post("/scoring", response_model=ConfigDetailResponse)
def save_scoring(
    request: ConfigSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save a Scoring configuration."""
    request.type = "scoring"
    config = _save_config("scoring", request, current_user, db)
    return config


@router.get("/list", response_model=list[ConfigListResponse])
def list_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all configurations for the current user."""
    configs = (
        db.query(Configuration)
        .filter(Configuration.user_id == current_user.id)
        .order_by(Configuration.created_at.desc())
        .all()
    )
    return configs


@router.get("/{config_id}", response_model=ConfigDetailResponse)
def get_config(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single configuration by ID."""
    config = db.query(Configuration).filter(Configuration.id == config_id).first()
    if not config:
        raise NotFoundError(detail=f"Configuration {config_id} not found")
    return config


@router.delete("/{config_id}")
def delete_config(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a configuration by ID."""
    config = (
        db.query(Configuration)
        .filter(Configuration.id == config_id, Configuration.user_id == current_user.id)
        .first()
    )
    if not config:
        raise NotFoundError(detail=f"Configuration {config_id} not found")

    db.delete(config)
    db.commit()
    return {"message": "Configuration deleted", "id": config_id}
