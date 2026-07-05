import os
import shutil
from uuid import uuid4

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.candidate import Candidate, CandidateSkill
from app.models.user import User
from app.utils.resume_parser import parse_resume


UPLOAD_DIR = "uploads/resumes"
ALLOWED_EXTENSIONS = [".pdf", ".docx"]


def validate_resume_file(file: UploadFile):
    _, extension = os.path.splitext(file.filename.lower())

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX resume files are allowed"
        )


def save_resume_file(file: UploadFile) -> tuple[str, str]:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    _, extension = os.path.splitext(file.filename.lower())
    unique_file_name = f"{uuid4()}{extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_file_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return unique_file_name, file_path


def upload_candidate_resume(
    file: UploadFile,
    current_user: User,
    db: Session
):
    validate_resume_file(file)

    saved_file_name, file_path = save_resume_file(file)

    try:
        extracted_data = parse_resume(file_path)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume parsing failed: {str(error)}"
        )

    candidate = Candidate(
        name=extracted_data.get("name"),
        email=extracted_data.get("email"),
        phone=extracted_data.get("phone"),
        total_experience=extracted_data.get("total_experience"),
        education=extracted_data.get("education"),
        resume_file_name=file.filename,
        resume_file_path=file_path,
        resume_text=extracted_data.get("resume_text"),
        uploaded_by=current_user.id
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    for skill in extracted_data.get("skills", []):
        candidate_skill = CandidateSkill(
            candidate_id=candidate.id,
            skill_name=skill
        )
        db.add(candidate_skill)

    db.commit()
    db.refresh(candidate)

    return candidate


def get_candidates(
    db: Session,
    search: str | None = None,
    skill: str | None = None,
    experience: str | None = None
):
    query = db.query(Candidate).options(joinedload(Candidate.skills))

    if search:
        search_value = f"%{search}%"
        query = query.filter(
            Candidate.name.like(search_value)
            | Candidate.email.like(search_value)
            | Candidate.phone.like(search_value)
        )

    if experience:
        query = query.filter(Candidate.total_experience.like(f"%{experience}%"))

    if skill:
        query = query.join(CandidateSkill).filter(
            CandidateSkill.skill_name.like(f"%{skill}%")
        )

    return query.order_by(Candidate.created_at.desc()).all()


def get_candidate_by_id(candidate_id: int, db: Session):
    candidate = (
        db.query(Candidate)
        .options(joinedload(Candidate.skills))
        .filter(Candidate.id == candidate_id)
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    return candidate


def delete_candidate(candidate_id: int, db: Session):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    if candidate.resume_file_path and os.path.exists(candidate.resume_file_path):
        os.remove(candidate.resume_file_path)

    db.delete(candidate)
    db.commit()

    return {
        "message": "Candidate deleted successfully"
    }