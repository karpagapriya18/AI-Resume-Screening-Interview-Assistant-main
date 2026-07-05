from sqlalchemy import Column, BigInteger, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class InterviewQuestionSet(Base):
    __tablename__ = "interview_question_sets"

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

    technical_questions = Column(Text, nullable=True)
    scenario_questions = Column(Text, nullable=True)
    behavioral_questions = Column(Text, nullable=True)
    raw_ai_response = Column(Text, nullable=True)

    generated_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CandidateSummary(Base):
    __tablename__ = "candidate_summaries"

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

    candidate_overview = Column(Text, nullable=True)
    skill_assessment = Column(Text, nullable=True)
    experience_summary = Column(Text, nullable=True)
    hiring_recommendation = Column(Text, nullable=True)
    raw_ai_response = Column(Text, nullable=True)

    generated_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())