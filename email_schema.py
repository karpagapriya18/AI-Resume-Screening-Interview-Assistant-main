from datetime import datetime
from pydantic import BaseModel, EmailStr


class InterviewInvitationRequest(BaseModel):
    candidate_id: int
    job_id: int
    recipient_email: EmailStr | None = None
    interview_datetime: str | None = None
    meeting_link: str | None = None
    custom_message: str | None = None


class InterviewInvitationResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    recipient_email: str
    subject: str
    message: str
    status: str
    sent_by: int
    created_at: datetime

    class Config:
        from_attributes = True
