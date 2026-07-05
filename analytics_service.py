from collections import defaultdict

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.candidate import Candidate
from app.models.job import JobDescription, JobSkill
from app.models.evaluation import ResumeEvaluation
from app.models.ai_output import InterviewQuestionSet, CandidateSummary


def get_dashboard_analytics(db: Session):
    total_candidates = db.query(Candidate).count()
    total_job_descriptions = db.query(JobDescription).count()
    total_evaluations = db.query(ResumeEvaluation).count()
    total_question_sets = db.query(InterviewQuestionSet).count()
    total_summaries = db.query(CandidateSummary).count()

    average_score = db.query(func.avg(ResumeEvaluation.match_score)).scalar()

    return {
        "total_candidates": total_candidates,
        "total_job_descriptions": total_job_descriptions,
        "total_evaluations": total_evaluations,
        "average_match_score": round(float(average_score or 0), 2),
        "total_interview_question_sets": total_question_sets,
        "total_candidate_summaries": total_summaries
    }


def get_recent_candidates(db: Session, limit: int = 10):
    return (
        db.query(Candidate)
        .order_by(Candidate.created_at.desc())
        .limit(limit)
        .all()
    )


def get_most_requested_skills(db: Session, limit: int = 10):
    results = (
        db.query(
            JobSkill.skill_name,
            func.count(JobSkill.id).label("request_count")
        )
        .group_by(JobSkill.skill_name)
        .order_by(desc("request_count"))
        .limit(limit)
        .all()
    )

    return [
        {
            "skill_name": row.skill_name,
            "request_count": row.request_count
        }
        for row in results
    ]


def get_most_active_users(db: Session, limit: int = 10):
    activity = defaultdict(lambda: {
        "uploaded_candidates": 0,
        "evaluations_created": 0,
        "questions_generated": 0,
        "summaries_generated": 0
    })

    candidate_uploads = (
        db.query(
            Candidate.uploaded_by,
            func.count(Candidate.id).label("count")
        )
        .group_by(Candidate.uploaded_by)
        .all()
    )

    for row in candidate_uploads:
        activity[row.uploaded_by]["uploaded_candidates"] = row.count

    evaluations = (
        db.query(
            ResumeEvaluation.evaluated_by,
            func.count(ResumeEvaluation.id).label("count")
        )
        .group_by(ResumeEvaluation.evaluated_by)
        .all()
    )

    for row in evaluations:
        activity[row.evaluated_by]["evaluations_created"] = row.count

    question_sets = (
        db.query(
            InterviewQuestionSet.generated_by,
            func.count(InterviewQuestionSet.id).label("count")
        )
        .group_by(InterviewQuestionSet.generated_by)
        .all()
    )

    for row in question_sets:
        activity[row.generated_by]["questions_generated"] = row.count

    summaries = (
        db.query(
            CandidateSummary.generated_by,
            func.count(CandidateSummary.id).label("count")
        )
        .group_by(CandidateSummary.generated_by)
        .all()
    )

    for row in summaries:
        activity[row.generated_by]["summaries_generated"] = row.count

    user_ids = list(activity.keys())

    if not user_ids:
        return []

    users = db.query(User).filter(User.id.in_(user_ids)).all()

    response = []

    for user in users:
        user_activity = activity[user.id]

        total_activity = (
            user_activity["uploaded_candidates"]
            + user_activity["evaluations_created"]
            + user_activity["questions_generated"]
            + user_activity["summaries_generated"]
        )

        response.append({
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "uploaded_candidates": user_activity["uploaded_candidates"],
            "evaluations_created": user_activity["evaluations_created"],
            "questions_generated": user_activity["questions_generated"],
            "summaries_generated": user_activity["summaries_generated"],
            "total_activity": total_activity
        })

    response.sort(key=lambda item: item["total_activity"], reverse=True)

    return response[:limit]


def get_resume_ranking_leaderboard(
    db: Session,
    job_id: int | None = None,
    limit: int = 10
):
    query = (
        db.query(
            ResumeEvaluation,
            Candidate,
            JobDescription
        )
        .join(Candidate, ResumeEvaluation.candidate_id == Candidate.id)
        .join(JobDescription, ResumeEvaluation.job_id == JobDescription.id)
    )

    if job_id:
        query = query.filter(ResumeEvaluation.job_id == job_id)

    results = (
        query
        .order_by(
            ResumeEvaluation.match_score.desc(),
            ResumeEvaluation.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    leaderboard = []

    for evaluation, candidate, job in results:
        leaderboard.append({
            "evaluation_id": evaluation.id,
            "candidate_id": candidate.id,
            "candidate_name": candidate.name,
            "candidate_email": candidate.email,
            "job_id": job.id,
            "job_title": job.job_title,
            "match_score": evaluation.match_score,
            "recommendation": evaluation.recommendation,
            "missing_skills": evaluation.missing_skills,
            "strengths": evaluation.strengths,
            "weaknesses": evaluation.weaknesses,
            "evaluated_at": evaluation.created_at
        })

    return leaderboard