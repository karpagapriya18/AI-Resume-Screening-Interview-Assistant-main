from sqlalchemy import Column, BigInteger, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class ResumeEvaluation(Base):
    __tablename__ = "resume_evaluations"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    candidate_id = Column(
        BigInteger,
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    job_id = Column(
        BigInteger,
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    match_score = Column(Float, nullable=False, default=0)

    missing_skills = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    raw_ai_response = Column(Text, nullable=True)

    evaluated_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())