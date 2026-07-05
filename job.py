from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    job_title = Column(String(200), nullable=False, index=True)
    experience_requirement = Column(String(100), nullable=True)
    location = Column(String(150), nullable=True)
    employment_type = Column(String(100), nullable=True)
    job_description_content = Column(Text, nullable=False)

    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    required_skills = relationship(
        "JobSkill",
        back_populates="job",
        cascade="all, delete-orphan"
    )


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    job_id = Column(
        BigInteger,
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False
    )

    skill_name = Column(String(100), nullable=False, index=True)

    job = relationship("JobDescription", back_populates="required_skills")