from langgraph.graph import StateGraph, END
from typing import TypedDict, Any
from jd_analyzer import analyze_job_description
from resume_screening import screen_resume
from resume_parser import parse_resume_file


class HRState(TypedDict):
    jd_text: str
    resume_filepath: str
    jd_output: Any
    resume_text: str
    resume_output: Any


workflow = StateGraph(HRState)


def jd_node(state: HRState):
    output = analyze_job_description.invoke(state["jd_text"])
    return {"jd_output": output}


def resume_parse_node(state: HRState):
    resume_text = parse_resume_file(state["resume_filepath"])
    return {"resume_text": resume_text}


def resume_screening_node(state: HRState):
    result = screen_resume.invoke({
        "jd_output": state["jd_output"],
        "resume_text": state["resume_text"]
    })
    return {"resume_output": result}


workflow.add_node("jd_analyzer", jd_node)
workflow.add_node("resume_parser", resume_parse_node)
workflow.add_node("resume_screening", resume_screening_node)

workflow.set_entry_point("jd_analyzer")

workflow.add_edge("jd_analyzer", "resume_parser")
workflow.add_edge("resume_parser", "resume_screening")
workflow.add_edge("resume_screening", END)

app = workflow.compile()
