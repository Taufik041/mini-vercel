import re
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, field_validator
from sqlmodel import Field, Relationship, SQLModel


class Project(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True)
    owner_id: uuid.UUID
    git_url: str | None = None
    status: str = Field(default="pending")
    live_url: str | None = None
    port: int = Field(default=3000)
    # change these two fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    env_vars: list["EnvVar"] = Relationship(back_populates="project")


class EnvVar(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.id")
    key: str
    value: str

    project: Project | None = Relationship(back_populates="env_vars")


class EnvVarIn(BaseModel):
    key: str
    value: str


class CreateProjectReq(BaseModel):
    name: str
    git_url: str | None = None
    port: int = 3000
    env_vars: list[EnvVarIn] = []

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]{3,30}$", v):
            raise ValueError(
                "name must be 3-30 chars, lowercase letters, numbers, hyphens only"
            )
        return v


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    git_url: str | None
    status: str
    live_url: str | None
    port: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
