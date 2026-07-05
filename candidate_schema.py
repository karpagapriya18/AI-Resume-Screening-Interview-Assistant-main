from datetime import datetime
from pydantic import BaseModel


class CandidateSkillResponse(BaseModel):
    id: int
    skill_name: str

    class Config:
        from_attributes = True


class CandidateResponse(BaseModel):
    id: int
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience: str | None = None
    education: str | None = None
    resume_file_name: str
    resume_file_path: str
    created_at: datetime
    skills: list[CandidateSkillResponse] = []

    class Config:
        from_attributes = True


class CandidateListResponse(BaseModel):
    id: int
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience: str | None = None
    resume_file_name: str
    created_at: datetime
    skills: list[CandidateSkillResponse] = []

    class Config:
        from_attributes = True