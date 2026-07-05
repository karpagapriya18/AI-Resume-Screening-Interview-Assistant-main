from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.candidate import Candidate


class CandidateEmbedding(Base):
    __tablename__ = "candidate_embeddings"

    id = Column(Integer, primary_key=True, index=True)

    candidate_id = Column(
        Candidate.__table__.c.id.type,
        ForeignKey("candidates.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    embedding_json = Column(Text, nullable=False)
    source_text = Column(Text, nullable=True)
    embedding_model = Column(String(120), nullable=False, default="local-hashing")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    candidate = relationship("Candidate")
