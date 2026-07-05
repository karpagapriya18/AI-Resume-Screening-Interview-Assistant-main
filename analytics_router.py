from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth_dependency import require_role
from app.models.user import User
from app.schemas.analytics_schema import (
    DashboardAnalyticsResponse,
    RecentCandidateResponse,
    RequestedSkillResponse,
    ActiveUserResponse,
    ResumeRankingResponse
)
from app.services.analytics_service import (
    get_dashboard_analytics,
    get_recent_candidates,
    get_most_requested_skills,
    get_most_active_users,
    get_resume_ranking_leaderboard
)


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics Dashboard"]
)


@router.get("/", response_model=DashboardAnalyticsResponse)
def dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR"]))
):
    return get_dashboard_analytics(db)


@router.get("/recent-candidates", response_model=list[RecentCandidateResponse])
def recent_candidates(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return get_recent_candidates(db, limit)


@router.get("/most-requested-skills", response_model=list[RequestedSkillResponse])
def most_requested_skills(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR"]))
):
    return get_most_requested_skills(db, limit)


@router.get("/most-active-users", response_model=list[ActiveUserResponse])
def most_active_users(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR"]))
):
    return get_most_active_users(db, limit)


@router.get("/resume-ranking", response_model=list[ResumeRankingResponse])
def resume_ranking_leaderboard(
    job_id: int | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return get_resume_ranking_leaderboard(db, job_id, limit)