# app/routes/preference.py — Book Preference endpoints for students

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_student
from app.schemas.preference import PreferenceCreate
from app.services import preference_service

router = APIRouter()


@router.get("/preferences")
def get_preferences(
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Get all book preferences for the current student."""
    prefs = preference_service.get_preferences(db, claims["id"])
    return {"preferences": prefs, "total": len(prefs)}


@router.post("/preferences")
def add_preference(
    data: PreferenceCreate,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Add a new book preference."""
    return preference_service.add_preference(
        db,
        student_id=claims["id"],
        preference_type=data.preference_type,
        preference_value=data.preference_value,
    )


@router.delete("/preferences/{preference_id}")
def remove_preference(
    preference_id: int,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Remove a book preference."""
    return preference_service.remove_preference(db, preference_id, claims["id"])
