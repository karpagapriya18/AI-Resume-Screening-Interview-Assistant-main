from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth_dependency import require_role
from app.models.user import User
from app.schemas.email_schema import (
    InterviewInvitationRequest,
    InterviewInvitationResponse,
)
from app.services.email_service import (
    get_invitation_history,
    send_interview_invitation,
)


router = APIRouter(
    prefix="/invitations",
    tags=["Interview Invitations"]
)


@router.post("/send", response_model=InterviewInvitationResponse)
def send_invitation(
    data: InterviewInvitationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return send_interview_invitation(data, current_user, db)


@router.get("/history", response_model=list[InterviewInvitationResponse])
def invitation_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return get_invitation_history(db)
