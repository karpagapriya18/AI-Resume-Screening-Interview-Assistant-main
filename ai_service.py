import json
import re

from fastapi import HTTPException, status
from google import genai
from google.genai import types
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models.candidate import Candidate
from app.models.job import JobDescription
from app.models.evaluation import ResumeEvaluation
from app.models.user import User
from app.schemas.ai_schema import ResumeMatchRequest
from app.models.ai_output import InterviewQuestionSet, CandidateSummary


def get_gemini_client():
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        return None

    return genai.Client(api_key=settings.GEMINI_API_KEY)


def get_candidate(candidate_id: int, db: Session):
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


def get_job(job_id: int, db: Session):
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


def build_resume_match_prompt(candidate: Candidate, job: JobDescription) -> str:
    candidate_skills = [skill.skill_name for skill in candidate.skills]
    job_skills = [skill.skill_name for skill in job.required_skills]

    resume_text = candidate.resume_text or ""

    if len(resume_text) > 10000:
        resume_text = resume_text[:10000]

    return f"""
You are an expert HR resume screening assistant.

Analyze the candidate resume against the job description.

Return ONLY valid JSON. Do not include markdown, comments, explanation, or extra text.

Required JSON format:
{{
  "match_score": 85,
  "missing_skills": "Docker, AWS",
  "strengths": "Strong Python and FastAPI experience. Good backend project exposure.",
  "weaknesses": "Limited cloud deployment experience.",
  "recommendation": "Recommended for first-round interview",
  "ai_summary": "Candidate is suitable for the Python Developer role with strong backend skills."
}}

Scoring rules:
- match_score must be from 0 to 100.
- Consider skills, experience, education, resume quality, and role suitability.
- If resume information is insufficient, reduce the score and mention that clearly.
- Be practical and recruiter-friendly.

Candidate Details:
Name: {candidate.name}
Email: {candidate.email}
Phone: {candidate.phone}
Extracted Skills: {candidate_skills}
Experience: {candidate.total_experience}
Education: {candidate.education}

Resume Text:
{resume_text}

Job Details:
Job Title: {job.job_title}
Required Skills: {job_skills}
Experience Requirement: {job.experience_requirement}
Location: {job.location}
Employment Type: {job.employment_type}
Job Description:
{job.job_description_content}
"""


def extract_json_from_ai_response(response_text: str) -> dict:
    if not response_text:
        raise ValueError("Empty AI response")

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

    if not json_match:
        raise ValueError("AI response was not valid JSON")

    return json.loads(json_match.group(0))


def normalize_match_score(value) -> float:
    try:
        score = float(value)
    except Exception:
        score = 0

    if score < 0:
        score = 0

    if score > 100:
        score = 100

    return score


def generate_local_match(candidate: Candidate, job: JobDescription) -> dict:
    candidate_skills = {
        skill.skill_name.strip().lower()
        for skill in candidate.skills
        if skill.skill_name
    }

    job_skills = {
        skill.skill_name.strip().lower()
        for skill in job.required_skills
        if skill.skill_name
    }

    matched_skills = sorted(candidate_skills.intersection(job_skills))
    missing_skills = sorted(job_skills.difference(candidate_skills))

    if job_skills:
        skill_score = (len(matched_skills) / len(job_skills)) * 100
    else:
        skill_score = 50

    resume_text = (candidate.resume_text or "").lower()

    job_title_words = [
        word.lower()
        for word in job.job_title.split()
        if len(word) > 2
    ]

    title_match_bonus = 0

    for word in job_title_words:
        if word in resume_text:
            title_match_bonus += 5

    score = min(skill_score + title_match_bonus, 100)

    if score >= 80:
        recommendation = "Recommended for interview"
    elif score >= 60:
        recommendation = "Can be considered after skill review"
    elif score >= 40:
        recommendation = "Needs further evaluation"
    else:
        recommendation = "Not recommended for this role"

    if matched_skills:
        strengths = "Candidate matches these required skills: " + ", ".join(
            skill.title() for skill in matched_skills
        )
    else:
        strengths = "No strong required skill match found from extracted resume data."

    if missing_skills:
        weaknesses = "Candidate is missing these required skills: " + ", ".join(
            skill.title() for skill in missing_skills
        )
        missing_skills_text = ", ".join(skill.title() for skill in missing_skills)
    else:
        weaknesses = "No major required skills missing based on extracted data."
        missing_skills_text = "No major missing skills"

    ai_summary = (
        f"Local analysis shows a match score of {round(score, 2)}%. "
        f"The candidate matched {len(matched_skills)} out of {len(job_skills)} required skills. "
        f"This result was generated by the local fallback engine."
    )

    return {
        "match_score": round(score, 2),
        "missing_skills": missing_skills_text,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendation": recommendation,
        "ai_summary": ai_summary,
        "raw_ai_response": "Generated by local fallback matching engine"
    }


def generate_gemini_match(candidate: Candidate, job: JobDescription) -> dict:
    client = get_gemini_client()

    if client is None:
        return generate_local_match(candidate, job)

    prompt = build_resume_match_prompt(candidate, job)

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
            max_output_tokens=1200
        )
    )

    response_text = response.text

    parsed = extract_json_from_ai_response(response_text)
    parsed["raw_ai_response"] = response_text

    return parsed


def generate_resume_match(
    data: ResumeMatchRequest,
    current_user: User,
    db: Session
):
    candidate = get_candidate(data.candidate_id, db)
    job = get_job(data.job_id, db)

    try:
        parsed = generate_gemini_match(candidate, job)
    except Exception as error:
        error_message = str(error).lower()

        if (
            "quota" in error_message
            or "rate" in error_message
            or "429" in error_message
            or "api key" in error_message
            or "permission" in error_message
        ):
            parsed = generate_local_match(candidate, job)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gemini matching failed: {str(error)}"
            )

    evaluation = ResumeEvaluation(
        candidate_id=candidate.id,
        job_id=job.id,
        match_score=normalize_match_score(parsed.get("match_score")),
        missing_skills=parsed.get("missing_skills"),
        strengths=parsed.get("strengths"),
        weaknesses=parsed.get("weaknesses"),
        recommendation=parsed.get("recommendation"),
        ai_summary=parsed.get("ai_summary"),
        raw_ai_response=parsed.get("raw_ai_response"),
        evaluated_by=current_user.id
    )

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return evaluation


def get_evaluations(db: Session):
    return (
        db.query(ResumeEvaluation)
        .order_by(ResumeEvaluation.created_at.desc())
        .all()
    )


def get_evaluation_by_id(evaluation_id: int, db: Session):
    evaluation = (
        db.query(ResumeEvaluation)
        .filter(ResumeEvaluation.id == evaluation_id)
        .first()
    )

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )



    return evaluation


def build_interview_question_prompt(candidate: Candidate, job: JobDescription) -> str:
    candidate_skills = [skill.skill_name for skill in candidate.skills]
    job_skills = [skill.skill_name for skill in job.required_skills]

    resume_text = candidate.resume_text or ""

    if len(resume_text) > 8000:
        resume_text = resume_text[:8000]

    return f"""
You are an expert technical recruiter and interview designer.

Generate interview questions for this candidate based on their resume and the job description.

Return ONLY valid JSON. No markdown. No explanation.

Required JSON format:
{{
  "technical_questions": [
    "Question 1",
    "Question 2",
    "Question 3",
    "Question 4",
    "Question 5"
  ],
  "scenario_questions": [
    "Question 1",
    "Question 2",
    "Question 3"
  ],
  "behavioral_questions": [
    "Question 1",
    "Question 2",
    "Question 3"
  ]
}}

Rules:
- Questions must match the candidate skill level.
- Include questions based on candidate skills, experience, and job description.
- Technical questions should test role-specific knowledge.
- Scenario questions should test real-world problem solving.
- Behavioral questions should test communication, teamwork, ownership, and learning mindset.
- If resume information is insufficient, generate basic screening questions and mention gaps indirectly.

Candidate Details:
Name: {candidate.name}
Skills: {candidate_skills}
Experience: {candidate.total_experience}
Education: {candidate.education}

Resume Text:
{resume_text}

Job Details:
Title: {job.job_title}
Required Skills: {job_skills}
Experience Requirement: {job.experience_requirement}
Description:
{job.job_description_content}
"""


def build_candidate_summary_prompt(candidate: Candidate, job: JobDescription) -> str:
    candidate_skills = [skill.skill_name for skill in candidate.skills]
    job_skills = [skill.skill_name for skill in job.required_skills]

    resume_text = candidate.resume_text or ""

    if len(resume_text) > 8000:
        resume_text = resume_text[:8000]

    return f"""
You are an expert HR resume screening assistant.

Generate a candidate summary for the selected job role.

Return ONLY valid JSON. No markdown. No explanation.

Required JSON format:
{{
  "candidate_overview": "Short overview of the candidate.",
  "skill_assessment": "Assessment of candidate skills against the job.",
  "experience_summary": "Summary of work experience and relevance.",
  "hiring_recommendation": "Clear hiring recommendation."
}}

Rules:
- Be professional and recruiter-friendly.
- Highlight suitability for the role.
- Mention missing information if the resume lacks enough detail.
- If insufficient information is available, clearly say that the recommendation is limited.

Candidate Details:
Name: {candidate.name}
Email: {candidate.email}
Phone: {candidate.phone}
Skills: {candidate_skills}
Experience: {candidate.total_experience}
Education: {candidate.education}

Resume Text:
{resume_text}

Job Details:
Title: {job.job_title}
Required Skills: {job_skills}
Experience Requirement: {job.experience_requirement}
Location: {job.location}
Employment Type: {job.employment_type}
Description:
{job.job_description_content}
"""


def list_to_text(value) -> str:
    if isinstance(value, list):
        return "\n".join([f"{index + 1}. {item}" for index, item in enumerate(value)])

    if isinstance(value, str):
        return value

    return ""


def generate_local_questions(candidate: Candidate, job: JobDescription) -> dict:
    candidate_skills = [skill.skill_name for skill in candidate.skills]
    job_skills = [skill.skill_name for skill in job.required_skills]

    main_skills = job_skills if job_skills else candidate_skills

    if not main_skills:
        main_skills = ["problem solving", "communication", "basic technical knowledge"]

    technical_questions = []

    for skill in main_skills[:5]:
        technical_questions.append(
            f"Explain your experience with {skill} and describe one project where you used it."
        )

    while len(technical_questions) < 5:
        technical_questions.append(
            "Explain one technical challenge you faced in a project and how you solved it."
        )

    scenario_questions = [
        f"You are assigned to work on a {job.job_title} task with a short deadline. How would you plan and complete it?",
        "If you find a bug in production, what steps would you follow to investigate and fix it?",
        "How would you learn a new technology required for this role within a short time?"
    ]

    behavioral_questions = [
        "Tell me about a time you worked as part of a team.",
        "Tell me about a time you received feedback and improved your work.",
        "Why are you interested in this role?"
    ]

    return {
        "technical_questions": technical_questions,
        "scenario_questions": scenario_questions,
        "behavioral_questions": behavioral_questions,
        "raw_ai_response": "Generated by local fallback question generator"
    }


def generate_local_summary(candidate: Candidate, job: JobDescription) -> dict:
    candidate_skills = [skill.skill_name for skill in candidate.skills]
    job_skills = [skill.skill_name for skill in job.required_skills]

    candidate_skill_set = {skill.lower() for skill in candidate_skills}
    job_skill_set = {skill.lower() for skill in job_skills}

    matched = candidate_skill_set.intersection(job_skill_set)
    missing = job_skill_set.difference(candidate_skill_set)

    overview = (
        f"{candidate.name or 'The candidate'} has uploaded a resume for evaluation "
        f"against the {job.job_title} role."
    )

    if candidate.total_experience:
        overview += f" The resume indicates around {candidate.total_experience} of experience."

    if candidate_skills:
        skill_assessment = (
            "Extracted candidate skills include: "
            + ", ".join(candidate_skills)
            + "."
        )
    else:
        skill_assessment = (
            "The resume does not provide enough clearly extracted skills for detailed assessment."
        )

    if matched:
        skill_assessment += (
            " Matching job skills: "
            + ", ".join(skill.title() for skill in matched)
            + "."
        )

    if missing:
        skill_assessment += (
            " Missing or unclear skills: "
            + ", ".join(skill.title() for skill in missing)
            + "."
        )

    experience_summary = (
        candidate.total_experience
        if candidate.total_experience
        else "Experience details are insufficient or not clearly extracted from the resume."
    )

    if missing:
        hiring_recommendation = (
            "Candidate can be considered for screening, but missing skills should be validated during interview."
        )
    else:
        hiring_recommendation = (
            "Candidate appears suitable for initial interview based on extracted resume data."
        )

    return {
        "candidate_overview": overview,
        "skill_assessment": skill_assessment,
        "experience_summary": experience_summary,
        "hiring_recommendation": hiring_recommendation,
        "raw_ai_response": "Generated by local fallback summary generator"
    }


def generate_gemini_questions(candidate: Candidate, job: JobDescription) -> dict:
    client = get_gemini_client()

    if client is None:
        return generate_local_questions(candidate, job)

    prompt = build_interview_question_prompt(candidate, job)

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,
            max_output_tokens=1500
        )
    )

    response_text = response.text
    parsed = extract_json_from_ai_response(response_text)
    parsed["raw_ai_response"] = response_text

    return parsed


def generate_gemini_summary(candidate: Candidate, job: JobDescription) -> dict:
    client = get_gemini_client()

    if client is None:
        return generate_local_summary(candidate, job)

    prompt = build_candidate_summary_prompt(candidate, job)

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
            max_output_tokens=1200
        )
    )

    response_text = response.text
    parsed = extract_json_from_ai_response(response_text)
    parsed["raw_ai_response"] = response_text

    return parsed


def generate_interview_questions(data, current_user: User, db: Session):
    candidate = get_candidate(data.candidate_id, db)
    job = get_job(data.job_id, db)

    try:
        parsed = generate_gemini_questions(candidate, job)
    except Exception as error:
        error_message = str(error).lower()

        if (
            "quota" in error_message
            or "rate" in error_message
            or "429" in error_message
            or "api key" in error_message
            or "permission" in error_message
        ):
            parsed = generate_local_questions(candidate, job)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Interview question generation failed: {str(error)}"
            )

    question_set = InterviewQuestionSet(
        candidate_id=candidate.id,
        job_id=job.id,
        technical_questions=list_to_text(parsed.get("technical_questions")),
        scenario_questions=list_to_text(parsed.get("scenario_questions")),
        behavioral_questions=list_to_text(parsed.get("behavioral_questions")),
        raw_ai_response=parsed.get("raw_ai_response"),
        generated_by=current_user.id
    )

    db.add(question_set)
    db.commit()
    db.refresh(question_set)

    return question_set


def generate_candidate_summary(data, current_user: User, db: Session):
    candidate = get_candidate(data.candidate_id, db)
    job = get_job(data.job_id, db)

    try:
        parsed = generate_gemini_summary(candidate, job)
    except Exception as error:
        error_message = str(error).lower()

        if (
            "quota" in error_message
            or "rate" in error_message
            or "429" in error_message
            or "api key" in error_message
            or "permission" in error_message
        ):
            parsed = generate_local_summary(candidate, job)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Candidate summary generation failed: {str(error)}"
            )

    summary = CandidateSummary(
        candidate_id=candidate.id,
        job_id=job.id,
        candidate_overview=parsed.get("candidate_overview"),
        skill_assessment=parsed.get("skill_assessment"),
        experience_summary=parsed.get("experience_summary"),
        hiring_recommendation=parsed.get("hiring_recommendation"),
        raw_ai_response=parsed.get("raw_ai_response"),
        generated_by=current_user.id
    )

    db.add(summary)
    db.commit()
    db.refresh(summary)

    return summary


def get_question_history(db: Session):
    return (
        db.query(InterviewQuestionSet)
        .order_by(InterviewQuestionSet.created_at.desc())
        .all()
    )


def get_summary_history(db: Session):
    return (
        db.query(CandidateSummary)
        .order_by(CandidateSummary.created_at.desc())
        .all()
    )