from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    name = Column(String(150), nullable=True)
    email = Column(String(150), nullable=True, index=True)
    phone = Column(String(50), nullable=True)

    total_experience = Column(String(100), nullable=True)
    education = Column(Text, nullable=True)

    resume_file_name = Column(String(255), nullable=False)
    resume_file_path = Column(String(500), nullable=False)
    resume_text = Column(Text, nullable=True)

    uploaded_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    skills = relationship(
        "CandidateSkill",
        back_populates="candidate",
        cascade="all, delete-orphan"
    )


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    candidate_id = Column(
        BigInteger,
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False
    )

    skill_name = Column(String(100), nullable=False, index=True)

    candidate = relationship("Candidate", back_populates="skills")