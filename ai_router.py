from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import time
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.dependencies.auth_dependency import require_role
from app.models.user import User
from app.schemas.ai_schema import (
    ResumeMatchRequest,
    ResumeMatchResponse,
    EvaluationListResponse,
    AIQuestionRequest,
    AIQuestionResponse,
    AISummaryRequest,
    AISummaryResponse
)
from app.services.ai_service import (
    generate_resume_match,
    get_evaluations,
    get_evaluation_by_id,
    generate_interview_questions,
    generate_candidate_summary,
    get_question_history,
    get_summary_history
)


router = APIRouter(
    prefix="/ai",
    tags=["AI Resume Screening"]
)


@router.post("/match", response_model=ResumeMatchResponse)
def match_resume_with_job(
    data: ResumeMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return generate_resume_match(data, current_user, db)


@router.get("/evaluations", response_model=list[EvaluationListResponse])
def list_evaluations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return get_evaluations(db)


@router.get("/evaluations/{evaluation_id}", response_model=ResumeMatchResponse)
def evaluation_details(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return get_evaluation_by_id(evaluation_id, db)


@router.post("/questions", response_model=AIQuestionResponse)
def create_interview_questions(
    data: AIQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return generate_interview_questions(data, current_user, db)


@router.post("/summary", response_model=AISummaryResponse)
def create_candidate_summary(
    data: AISummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return generate_candidate_summary(data, current_user, db)


@router.get("/questions/history", response_model=list[AIQuestionResponse])
def interview_question_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return get_question_history(db)


@router.get("/summaries/history", response_model=list[AISummaryResponse])
def candidate_summary_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return get_summary_history(db)

@router.get("/stream-demo")
def stream_ai_demo(
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    def generate():
        chunks = [
            "Analyzing candidate resume...\n",
            "Checking skills against job description...\n",
            "Calculating match score...\n",
            "Identifying strengths and weaknesses...\n",
            "Generating final recommendation...\n",
            "AI analysis completed.\n",
        ]

        for chunk in chunks:
            time.sleep(0.8)
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")