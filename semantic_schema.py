from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    skill_filter: list[str] | None = None
    min_score: float = 0
    limit: int = Field(default=10, ge=1, le=100)


class SemanticCandidateResult(BaseModel):
    candidate_id: int
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience: str | None = None
    education: str | None = None
    resume_file_name: str | None = None
    skills: list[str] = []
    matched_skills: list[str] = []
    score: float
    embedding_model: str
