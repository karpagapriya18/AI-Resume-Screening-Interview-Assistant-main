from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth_dependency import require_role
from app.models.user import User
from app.schemas.job_schema import (
    JobCreateRequest,
    JobUpdateRequest,
    JobResponse
)
from app.services.job_service import (
    create_job,
    get_jobs,
    get_job_by_id,
    update_job,
    delete_job
)


router = APIRouter(
    prefix="/jobs",
    tags=["Job Descriptions"]
)


@router.post("/", response_model=JobResponse)
def create_new_job(
    data: JobCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR"]))
):
    return create_job(data, current_user, db)


@router.get("/", response_model=list[JobResponse])
def list_jobs(
    search: str | None = Query(default=None),
    skill: str | None = Query(default=None),
    location: str | None = Query(default=None),
    employment_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return get_jobs(db, search, skill, location, employment_type)


@router.get("/{job_id}", response_model=JobResponse)
def job_details(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR", "Recruiter"]))
):
    return get_job_by_id(job_id, db)


@router.put("/{job_id}", response_model=JobResponse)
def edit_job(
    job_id: int,
    data: JobUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR"]))
):
    return update_job(job_id, data, db)


@router.delete("/{job_id}")
def remove_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["HR"]))
):
    return delete_job(job_id, db)