import smtplib
from email.message import EmailMessage

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.candidate import Candidate
from app.models.interview_invitation import InterviewInvitation
from app.models.job import JobDescription
from app.models.user import User
from app.schemas.email_schema import InterviewInvitationRequest


def build_interview_email(
    candidate: Candidate,
    job: JobDescription,
    data: InterviewInvitationRequest
):
    subject = f"Interview Invitation - {job.job_title}"

    candidate_name = candidate.name or "Candidate"

    message = f"""
Dear {candidate_name},

We are pleased to invite you for an interview for the role of {job.job_title}.

Job Details:
- Role: {job.job_title}
- Location: {job.location or "Not specified"}
- Employment Type: {job.employment_type or "Not specified"}
- Experience Requirement: {job.experience_requirement or "Not specified"}

Interview Schedule:
{data.interview_datetime or "The interview schedule will be shared shortly."}

Meeting Link:
{data.meeting_link or "The meeting link will be shared shortly."}

{data.custom_message or ""}

Please confirm your availability.

Regards,
HR Team
AI Resume Screening & Interview Assistant
""".strip()

    return subject, message


def send_smtp_email(to_email: str, subject: str, body: str):
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        return False

    email = EmailMessage()
    email["From"] = settings.SMTP_FROM_EMAIL
    email["To"] = to_email
    email["Subject"] = subject
    email.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()

        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        smtp.send_message(email)

    return True


def send_interview_invitation(
    data: InterviewInvitationRequest,
    current_user: User,
    db: Session
):
    candidate = db.query(Candidate).filter(Candidate.id == data.candidate_id).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    job = db.query(JobDescription).filter(JobDescription.id == data.job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )

    recipient_email = data.recipient_email or candidate.email

    if not recipient_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate email not found. Please provide recipient_email."
        )

    subject, message = build_interview_email(candidate, job, data)

    status_value = "drafted"

    try:
        sent = send_smtp_email(recipient_email, subject, message)
        status_value = "sent" if sent else "drafted"
    except Exception:
        status_value = "failed"

    invitation = InterviewInvitation(
        candidate_id=candidate.id,
        job_id=job.id,
        recipient_email=recipient_email,
        subject=subject,
        message=message,
        status=status_value,
        sent_by=current_user.id,
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    return invitation


def get_invitation_history(db: Session):
    return (
        db.query(InterviewInvitation)
        .order_by(InterviewInvitation.created_at.desc())
        .all()
    )
