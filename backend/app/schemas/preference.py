# app/schemas/preference.py — BookPreference request/response schemas

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class PreferenceCreate(BaseModel):
    preference_type: str = Field(..., min_length=1, max_length=20,
                                  description="One of: category, author, title")
    preference_value: str = Field(..., min_length=1, max_length=255)


class PreferenceResponse(BaseModel):
    id: int
    preference_type: str
    preference_value: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PreferenceListResponse(BaseModel):
    preferences: List[PreferenceResponse]
    total: int
