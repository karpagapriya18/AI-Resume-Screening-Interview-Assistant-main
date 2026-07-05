from datetime import datetime
from pydantic import BaseModel


class DashboardAnalyticsResponse(BaseModel):
    total_candidates: int
    total_job_descriptions: int
    total_evaluations: int
    average_match_score: float
    total_interview_question_sets: int
    total_candidate_summaries: int


class RecentCandidateResponse(BaseModel):
    id: int
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience: str | None = None
    resume_file_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class RequestedSkillResponse(BaseModel):
    skill_name: str
    request_count: int


class ActiveUserResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    role: str
    uploaded_candidates: int
    evaluations_created: int
    questions_generated: int
    summaries_generated: int
    total_activity: int


class ResumeRankingResponse(BaseModel):
    evaluation_id: int
    candidate_id: int
    candidate_name: str | None = None
    candidate_email: str | None = None
    job_id: int
    job_title: str
    match_score: float
    recommendation: str | None = None
    missing_skills: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    evaluated_at: datetime