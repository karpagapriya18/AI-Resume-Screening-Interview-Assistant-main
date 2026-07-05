from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth_dependency import get_current_user, require_role
from app.models.user import User
from app.schemas.candidate_schema import CandidateResponse, CandidateListResponse
from app.services.candidate_service import (
    upload_candidate_resume,
    get_candidates,
    get_candidate_by_id,
    delete_candidate
)


router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"]
)


@router.post("/upload", response_model=CandidateResponse)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR"]))
):
    return upload_candidate_resume(file, current_user, db)


@router.get("/", response_model=list[CandidateListResponse])
def list_candidates(
    search: str | None = Query(default=None),
    skill: str | None = Query(default=None),
    experience: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return get_candidates(db, search, skill, experience)


@router.get("/{candidate_id}", response_model=CandidateResponse)
def candidate_details(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return get_candidate_by_id(candidate_id, db)


@router.delete("/{candidate_id}")
def remove_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR"]))
):
    return delete_candidate(candidate_id, db)