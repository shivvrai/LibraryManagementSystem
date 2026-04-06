# app/schemas/auth.py — Authentication request/response schemas

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user: dict


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9._]+$")
    password: str = Field(..., min_length=4)
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(default="", max_length=100)
    phone: str = Field(default="", max_length=20)


class UsernameCheckRequest(BaseModel):
    username: str = Field(..., min_length=1)


class UsernameCheckResponse(BaseModel):
    available: bool
    username: str
