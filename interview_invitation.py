from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.candidate import Candidate
from app.models.job import JobDescription
from app.models.user import User


class InterviewInvitation(Base):
    __tablename__ = "interview_invitations"

    id = Column(Integer, primary_key=True, index=True)

    candidate_id = Column(
        Candidate.__table__.c.id.type,
        ForeignKey("candidates.id"),
        nullable=False,
        index=True
    )

    job_id = Column(
        JobDescription.__table__.c.id.type,
        ForeignKey("job_descriptions.id"),
        nullable=False,
        index=True
    )

    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="drafted")

    sent_by = Column(
        User.__table__.c.id.type,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
