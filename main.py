from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.routers import (
    ai_router,
    analytics_router,
    auth_router,
    candidate_router,
    email_router,
    health_router,
    job_router,
    semantic_router,
)
from app.models import (
    ai_output,
    candidate,
    candidate_embedding,
    evaluation,
    interview_invitation,
    job,
    user,
)


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Resume Screening & Interview Assistant",
    description="AI-powered resume screening, candidate matching, interview generation, and hiring analytics system.",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router.router)
app.include_router(auth_router.router)
app.include_router(candidate_router.router)
app.include_router(job_router.router)
app.include_router(ai_router.router)
app.include_router(analytics_router.router)
app.include_router(semantic_router.router)
app.include_router(email_router.router)


@app.get("/")
def root():
    return {
        "message": "AI Resume Screening & Interview Assistant API is running"
    }
