from datetime import datetime
from pydantic import BaseModel, Field


class ResumeMatchRequest(BaseModel):
    candidate_id: int = Field(..., gt=0)
    job_id: int = Field(..., gt=0)


class ResumeMatchResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    match_score: float
    missing_skills: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    recommendation: str | None = None
    ai_summary: str | None = None
    evaluated_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationListResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    match_score: float
    recommendation: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AIQuestionRequest(BaseModel):
    candidate_id: int = Field(..., gt=0)
    job_id: int = Field(..., gt=0)


class AIQuestionResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    technical_questions: str | None = None
    scenario_questions: str | None = None
    behavioral_questions: str | None = None
    generated_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class AISummaryRequest(BaseModel):
    candidate_id: int = Field(..., gt=0)
    job_id: int = Field(..., gt=0)


class AISummaryResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    candidate_overview: str | None = None
    skill_assessment: str | None = None
    experience_summary: str | None = None
    hiring_recommendation: str | None = None
    generated_by: int
    created_at: datetime

    class Config:
        from_attributes = True