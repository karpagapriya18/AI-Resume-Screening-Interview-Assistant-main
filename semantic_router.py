from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth_dependency import require_role
from app.models.user import User
from app.schemas.semantic_schema import SemanticCandidateResult, SemanticSearchRequest
from app.services.embedding_service import (
    rebuild_all_candidate_embeddings,
    rebuild_single_candidate_embedding,
    semantic_candidate_search,
)


router = APIRouter(
    prefix="/semantic-search",
    tags=["Semantic Candidate Search"]
)


@router.post("/candidates", response_model=list[SemanticCandidateResult])
def search_candidates_with_embeddings(
    data: SemanticSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return semantic_candidate_search(data, db)


@router.post("/rebuild-all")
def rebuild_all_embeddings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR"]))
):
    return rebuild_all_candidate_embeddings(db)


@router.post("/rebuild/{candidate_id}")
def rebuild_candidate_embedding(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR"]))
):
    return rebuild_single_candidate_embedding(candidate_id, db)
