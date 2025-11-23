import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from interview_logic import start_interview, next_step

app = FastAPI()

# Allow React dev server
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


class StartInterviewRequest(BaseModel):
    role: str
    customRole: Optional[str] = None
    experience: str
    style: str
    maxQuestions: int
    resumeText: Optional[str] = None


class StartInterviewResponse(BaseModel):
    interviewId: str
    question: str


class AnswerRequest(BaseModel):
    interviewId: str
    answer: Optional[str] = None
    end: bool = False


class AnswerResponse(BaseModel):
    done: bool
    nextQuestion: Optional[str] = None
    feedbackMarkdown: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/start-interview", response_model=StartInterviewResponse)
def api_start_interview(body: StartInterviewRequest):
    try:
        result = start_interview(
            role=body.role,
            custom_role=body.customRole,
            experience=body.experience,
            style=body.style,
            max_questions=body.maxQuestions,
            resume_text=body.resumeText,
        )
        return StartInterviewResponse(
            interviewId=result["interview_id"],
            question=result["question"],
        )
    except Exception as e:
        # Good for debugging when something goes wrong
        raise HTTPException(status_code=500, detail=f"start_interview failed: {str(e)}")


@app.post("/answer", response_model=AnswerResponse)
def api_answer(body: AnswerRequest):
    try:
        result = next_step(
            interview_id=body.interviewId,
            answer=body.answer,
            end=body.end,
        )
        return AnswerResponse(
            done=result["done"],
            nextQuestion=result["nextQuestion"],
            feedbackMarkdown=result["feedbackMarkdown"],
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Interview not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"next_step failed: {str(e)}")

