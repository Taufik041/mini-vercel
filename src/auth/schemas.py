from pydantic import BaseModel, EmailStr
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    email: str
    creds: float
    password: str
    is_active: bool


class SignUpReq(BaseModel):
    name: str
    email: EmailStr
    creds: float
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
