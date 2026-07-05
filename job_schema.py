from datetime import datetime
from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    job_title: str = Field(..., min_length=2, max_length=200)
    required_skills: list[str] = []
    experience_requirement: str | None = None
    location: str | None = None
    employment_type: str | None = None
    job_description_content: str = Field(..., min_length=10)


class JobUpdateRequest(BaseModel):
    job_title: str | None = None
    required_skills: list[str] | None = None
    experience_requirement: str | None = None
    location: str | None = None
    employment_type: str | None = None
    job_description_content: str | None = None


class JobSkillResponse(BaseModel):
    id: int
    skill_name: str

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    id: int
    job_title: str
    experience_requirement: str | None = None
    location: str | None = None
    employment_type: str | None = None
    job_description_content: str
    created_by: int
    created_at: datetime
    updated_at: datetime | None = None
    required_skills: list[JobSkillResponse] = []

    class Config:
        from_attributes = True