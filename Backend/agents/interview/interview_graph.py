from typing import TypedDict, List, Any, Dict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


llm = ChatOpenAI(model="gpt-4o-mini")  # or your chosen model


class AnswerEvaluation(TypedDict):
    question: str
    transcript: str
    content_score: int
    communication_score: int
    confidence_score: int
    cheating_flag: bool
    comments: str


class InterviewState(TypedDict):
    jd_output: Dict[str, Any]
    resume_output: Dict[str, Any]
    questions: List[str]
    current_index: int
    answers: List[AnswerEvaluation]
    last_answer: AnswerEvaluation | None
    final_decision: str  # "PASS" / "FAIL" / ""
    schedule_interview: bool




workflow = StateGraph(InterviewState)


def question_generator_node(state: InterviewState):
    # if questions already generated, just return state
    if state.get("questions"):
        return {}

    jd = state["jd_output"]
    resume = state["resume_output"]

    prompt = f"""
    You are an AI interviewer. Based on this job description and candidate profile,
    generate 5 technical + 2 behavioral interview questions.

    JOB DESCRIPTION:
    {jd}

    CANDIDATE RESUME SUMMARY:
    {resume}

    Return a JSON list of questions only, no explanation.
    """

    resp = llm.invoke(prompt)
    # You can parse resp.content as JSON; for now assume it's a list in text form
    # In real code, use json.loads(resp.content)
    questions = [q.strip("- ").strip() for q in resp.content.split("\n") if q.strip()]

    return {"questions": questions, "current_index": 0, "answers": [], "final_decision": "", "schedule_interview": False}


workflow.add_node("question_generator", question_generator_node)
workflow.set_entry_point("question_generator")


def answer_evaluator_node(state: InterviewState):
    idx = state["current_index"]
    if idx >= len(state["questions"]):
        # no more questions, do nothing here
        return {}

    question = state["questions"][idx]
    last_answer = state["last_answer"]  # will be filled from API with transcript & metrics

    # last_answer should contain:
    # {
    #   "transcript": str,
    #   "audio_metrics": {...}
    # }

    transcript = last_answer["transcript"]
    audio_metrics = last_answer.get("audio_metrics", {})

    prompt = f"""
    You are an expert technical interviewer and communication coach.

    QUESTION:
    {question}

    CANDIDATE ANSWER (TRANSCRIPT):
    {transcript}

    AUDIO METRICS (approximate):
    {audio_metrics}

    Evaluate:
    1. Content correctness and depth (0-10)
    2. Communication clarity & structure (0-10)
    3. Confidence (0-10) based on fluency, hesitation, etc.
    4. Is there any sign of cheating (reading exact script, unrelated answer, etc.)? (true/false)
    5. Short comments for HR.

    Return STRICT JSON:
    {{
      "content_score": int,
      "communication_score": int,
      "confidence_score": int,
      "cheating_flag": bool,
      "comments": "..."
    }}
    """

    resp = llm.invoke(prompt)
    # parse resp.content JSON in real implementation
    # pretend we parsed it:
    eval_json = {
        "content_score": 8,
        "communication_score": 7,
        "confidence_score": 8,
        "cheating_flag": False,
        "comments": "Good understanding, fairly confident."
    }

    evaluated: AnswerEvaluation = {
        "question": question,
        "transcript": transcript,
        **eval_json
    }

    answers = state["answers"] + [evaluated]
    new_index = idx + 1

    return {"answers": answers, "current_index": new_index, "last_answer": evaluated}


workflow.add_node("answer_evaluator", answer_evaluator_node)
workflow.add_edge("question_generator", "answer_evaluator")


def decision_node(state: InterviewState):
    answers = state["answers"]
    if not answers:
        return {"final_decision": "FAIL", "schedule_interview": False}

    avg_content = sum(a["content_score"] for a in answers) / len(answers)
    avg_comm = sum(a["communication_score"] for a in answers) / len(answers)
    avg_conf = sum(a["confidence_score"] for a in answers) / len(answers)
    cheating = any(a["cheating_flag"] for a in answers)

    # Simple rule-based logic (you can tune thresholds)
    if cheating:
        final = "FAIL"
        schedule = False
    elif avg_content >= 7 and avg_comm >= 7 and avg_conf >= 7:
        final = "PASS"
        schedule = True
    else:
        final = "FAIL"
        schedule = False

    return {
        "final_decision": final,
        "schedule_interview": schedule
    }


workflow.add_node("decision", decision_node)
workflow.add_edge("answer_evaluator", "decision")
workflow.add_edge("decision", END)

interview_app = workflow.compile()
