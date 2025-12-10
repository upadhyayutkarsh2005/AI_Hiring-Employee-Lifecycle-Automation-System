from fastapi import FastAPI, HTTPException, UploadFile, File, Form , APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from uuid import uuid4


from agents.interview.interview_graph import (
    InterviewState,
    AnswerEvaluation,
    question_generator_node,
    answer_evaluator_node,
    decision_node,
)
router = APIRouter()
# In-memory session store for now (later you can move this to MongoDB)
SESSIONS: Dict[str, InterviewState] = {}


# ---------- Helpers ----------

def create_initial_state(jd_output: Dict[str, Any],
                         resume_output: Dict[str, Any]) -> InterviewState:
    """Create an empty InterviewState for a new candidate."""
    return {
        "jd_output": jd_output,
        "resume_output": resume_output,
        "questions": [],
        "current_index": 0,
        "answers": [],
        "last_answer": None,
        "final_decision": "",
        "schedule_interview": False,
    }


def dummy_audio_metrics() -> Dict[str, Any]:
    """Placeholder: later compute real metrics from audio (pause ratio, speed, etc.)."""
    return {
        "speech_rate": "normal",
        "pauses": "moderate",
        "filler_words": "low",
    }


async def fake_transcribe_video(file: UploadFile) -> str:
    """
    Placeholder for video -> transcript.
    Later you will replace this with Whisper or another STT model.
    For now, we just return a dummy string.
    """
    # await file.read()  # you could save/read if needed
    return "This is a fake transcript from the candidate's video answer."


# ---------- Pydantic Schemas ----------

class StartInterviewRequest(BaseModel):
    jd_output: Dict[str, Any]
    resume_output: Dict[str, Any]


class StartInterviewResponse(BaseModel):
    session_id: str
    first_question: str
    total_questions: int


class AnswerResponse(BaseModel):
    done: bool
    current_index: int
    total_questions: int
    next_question: Optional[str] = None
    last_evaluation: Optional[AnswerEvaluation] = None
    final_decision: Optional[str] = None
    schedule_interview: Optional[bool] = None
    all_answers: Optional[List[AnswerEvaluation]] = None


# ---------- API Endpoints ----------

@router.post("/api/interview/start", response_model=StartInterviewResponse)
async def start_interview(payload: StartInterviewRequest):
    """
    Start a new AI interview session.
    - Takes JD + resume outputs (from your earlier agents)
    - Creates InterviewState
    - Generates questions via question_generator_node
    """
    state: InterviewState = create_initial_state(
        jd_output=payload.jd_output,
        resume_output=payload.resume_output,
    )

    # Run the question generator node once
    update = question_generator_node(state)
    state.update(update)

    if not state["questions"]:
        raise HTTPException(status_code=500, detail="Failed to generate interview questions.")

    session_id = str(uuid4())
    SESSIONS[session_id] = state

    return StartInterviewResponse(
        session_id=session_id,
        first_question=state["questions"][0],
        total_questions=len(state["questions"]),
    )


@router.post("/api/interview/answer", response_model=AnswerResponse)
async def submit_answer(
    session_id: str = Form(...),
    transcript: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    Submit an answer to the current question.
    For now you can pass either:
    - transcript (text answer), OR
    - video file (later you'll transcribe it with Whisper)

    The endpoint:
    - loads stored InterviewState
    - creates last_answer with transcript + dummy audio_metrics
    - calls answer_evaluator_node
    - if more questions -> returns next question
    - else -> calls decision_node and returns final result
    """
    # 1. Validate session
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Invalid session_id")

    state = SESSIONS[session_id]

    # 2. Get transcript (either direct text or from video)
    if transcript is None and file is None:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'transcript' text or a video file."
        )

    if transcript is None:
        # Later: replace with real STT
        transcript = await fake_transcribe_video(file)

    # 3. Build last_answer object expected by your graph node
    last_answer = {
        "transcript": transcript,
        "audio_metrics": dummy_audio_metrics(),
    }
    state["last_answer"] = last_answer  # type: ignore

    # 4. Evaluate this answer using your node
    update = answer_evaluator_node(state)
    state.update(update)

    current_index = state["current_index"]
    total_questions = len(state["questions"])
    last_eval = state["last_answer"]

    # 5. Check if we still have questions remaining
    if current_index < total_questions:
        # Not finished yet -> return next question
        next_q = state["questions"][current_index]
        SESSIONS[session_id] = state

        return AnswerResponse(
            done=False,
            current_index=current_index,
            total_questions=total_questions,
            next_question=next_q,
            last_evaluation=last_eval,  # type: ignore
        )

    # 6. No questions left -> compute final decision
    decision_update = decision_node(state)
    state.update(decision_update)
    SESSIONS[session_id] = state

    return AnswerResponse(
        done=True,
        current_index=current_index,
        total_questions=total_questions,
        last_evaluation=last_eval,  # type: ignore
        final_decision=state["final_decision"],
        schedule_interview=state["schedule_interview"],
        all_answers=state["answers"],
    )
