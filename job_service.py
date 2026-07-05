from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.job import JobDescription, JobSkill
from app.models.user import User
from app.schemas.job_schema import JobCreateRequest, JobUpdateRequest


def create_job(data: JobCreateRequest, current_user: User, db: Session):
    job = JobDescription(
        job_title=data.job_title,
        experience_requirement=data.experience_requirement,
        location=data.location,
        employment_type=data.employment_type,
        job_description_content=data.job_description_content,
        created_by=current_user.id
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    for skill in data.required_skills:
        if skill.strip():
            db.add(
                JobSkill(
                    job_id=job.id,
                    skill_name=skill.strip()
                )
            )

    db.commit()
    db.refresh(job)

    return get_job_by_id(job.id, db)


def get_jobs(
    db: Session,
    search: str | None = None,
    skill: str | None = None,
    location: str | None = None,
    employment_type: str | None = None
):
    query = db.query(JobDescription).options(
        joinedload(JobDescription.required_skills)
    )

    if search:
        search_value = f"%{search}%"
        query = query.filter(
            JobDescription.job_title.like(search_value)
            | JobDescription.job_description_content.like(search_value)
        )

    if location:
        query = query.filter(JobDescription.location.like(f"%{location}%"))

    if employment_type:
        query = query.filter(
            JobDescription.employment_type.like(f"%{employment_type}%")
        )

    if skill:
        query = query.join(JobSkill).filter(
            JobSkill.skill_name.like(f"%{skill}%")
        )

    return query.order_by(JobDescription.created_at.desc()).all()


def get_job_by_id(job_id: int, db: Session):
    job = (
        db.query(JobDescription)
        .options(joinedload(JobDescription.required_skills))
        .filter(JobDescription.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )

    return job


def update_job(job_id: int, data: JobUpdateRequest, db: Session):
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )

    if data.job_title is not None:
        job.job_title = data.job_title

    if data.experience_requirement is not None:
        job.experience_requirement = data.experience_requirement

    if data.location is not None:
        job.location = data.location

    if data.employment_type is not None:
        job.employment_type = data.employment_type

    if data.job_description_content is not None:
        job.job_description_content = data.job_description_content

    if data.required_skills is not None:
        db.query(JobSkill).filter(JobSkill.job_id == job.id).delete(
            synchronize_session=False
        )

        for skill in data.required_skills:
            if skill.strip():
                db.add(
                    JobSkill(
                        job_id=job.id,
                        skill_name=skill.strip()
                    )
                )

    db.commit()

    return get_job_by_id(job.id, db)


def delete_job(job_id: int, db: Session):
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )

    db.delete(job)
    db.commit()

    return {
        "message": "Job description deleted successfully"
    }