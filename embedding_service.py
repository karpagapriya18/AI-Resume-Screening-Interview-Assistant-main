import hashlib
import json
import math
import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.candidate import Candidate
from app.models.candidate_embedding import CandidateEmbedding
from app.schemas.semantic_schema import SemanticSearchRequest


def normalize_text(value: str | None) -> str:
    return str(value or "").lower().strip()


def tokenize(text: str):
    return re.findall(r"[a-zA-Z0-9+#.]+", normalize_text(text))


def normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))

    if norm == 0:
        return vector

    return [round(value / norm, 8) for value in vector]


def local_hash_embedding(text: str, dimensions: int = 768) -> list[float]:
    vector = [0.0] * dimensions

    for token in tokenize(text):
        hashed = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
        index = hashed % dimensions
        sign = 1 if ((hashed >> 8) & 1) == 0 else -1
        vector[index] += sign

    return normalize_vector(vector)


def gemini_embedding(text: str) -> list[float]:
    from google import genai
    from google.genai import types

    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    result = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=settings.EMBEDDING_DIMENSIONS
        ),
    )

    values = result.embeddings[0].values

    return normalize_vector([float(value) for value in values])


def generate_embedding(text: str) -> tuple[list[float], str]:
    provider = normalize_text(settings.EMBEDDING_PROVIDER)

    if provider == "gemini":
        try:
            return gemini_embedding(text), settings.GEMINI_EMBEDDING_MODEL
        except Exception:
            return local_hash_embedding(text, settings.EMBEDDING_DIMENSIONS), "local-hashing-fallback"

    return local_hash_embedding(text, settings.EMBEDDING_DIMENSIONS), "local-hashing"


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b:
        return 0.0

    length = min(len(vector_a), len(vector_b))

    return sum(vector_a[index] * vector_b[index] for index in range(length))


def get_candidate_skills(candidate: Candidate) -> list[str]:
    return [skill.skill_name for skill in candidate.skills or [] if skill.skill_name]


def build_candidate_search_text(candidate: Candidate) -> str:
    skills = " ".join(get_candidate_skills(candidate))

    return f"""
    Candidate Name: {candidate.name or ""}
    Email: {candidate.email or ""}
    Phone: {candidate.phone or ""}
    Experience: {candidate.total_experience or ""}
    Education: {candidate.education or ""}
    Resume File: {candidate.resume_file_name or ""}
    Skills: {skills}
    """


def create_or_update_candidate_embedding(candidate: Candidate, db: Session):
    source_text = build_candidate_search_text(candidate)
    embedding, model_name = generate_embedding(source_text)

    existing = (
        db.query(CandidateEmbedding)
        .filter(CandidateEmbedding.candidate_id == candidate.id)
        .first()
    )

    if existing:
        existing.source_text = source_text
        existing.embedding_json = json.dumps(embedding)
        existing.embedding_model = model_name
        db.commit()
        db.refresh(existing)
        return existing

    record = CandidateEmbedding(
        candidate_id=candidate.id,
        source_text=source_text,
        embedding_json=json.dumps(embedding),
        embedding_model=model_name,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


def rebuild_all_candidate_embeddings(db: Session):
    candidates = db.query(Candidate).all()

    for candidate in candidates:
        create_or_update_candidate_embedding(candidate, db)

    return {
        "message": "Candidate embeddings rebuilt successfully",
        "total_candidates": len(candidates),
    }


def ensure_candidate_embeddings(db: Session):
    candidates = db.query(Candidate).all()

    for candidate in candidates:
        existing = (
            db.query(CandidateEmbedding)
            .filter(CandidateEmbedding.candidate_id == candidate.id)
            .first()
        )

        if not existing:
            create_or_update_candidate_embedding(candidate, db)


def semantic_candidate_search(data: SemanticSearchRequest, db: Session):
    ensure_candidate_embeddings(db)

    query_text = data.query

    if data.skill_filter:
        query_text += " " + " ".join(data.skill_filter)

    query_embedding, _ = generate_embedding(query_text)

    records = db.query(CandidateEmbedding).join(Candidate).all()

    results = []

    requested_skills = [
        normalize_text(skill)
        for skill in data.skill_filter or []
        if normalize_text(skill)
    ]

    for record in records:
        candidate = record.candidate

        if not candidate:
            continue

        candidate_embedding = json.loads(record.embedding_json)
        raw_score = cosine_similarity(query_embedding, candidate_embedding)

        score = max(0, raw_score) * 100

        candidate_skills = get_candidate_skills(candidate)
        normalized_candidate_skills = [normalize_text(skill) for skill in candidate_skills]

        matched_skills = []

        for required_skill in requested_skills:
            for candidate_skill in normalized_candidate_skills:
                if required_skill in candidate_skill or candidate_skill in required_skill:
                    matched_skills.append(required_skill)
                    score += 8
                    break

        if score < data.min_score:
            continue

        results.append({
            "candidate_id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "total_experience": candidate.total_experience,
            "education": candidate.education,
            "resume_file_name": candidate.resume_file_name,
            "skills": candidate_skills,
            "matched_skills": sorted(list(set(matched_skills))),
            "score": round(min(score, 100), 2),
            "embedding_model": record.embedding_model,
        })

    results.sort(key=lambda item: item["score"], reverse=True)

    return results[:data.limit]


def rebuild_single_candidate_embedding(candidate_id: int, db: Session):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    create_or_update_candidate_embedding(candidate, db)

    return {
        "message": "Candidate embedding rebuilt successfully",
        "candidate_id": candidate_id,
    }
