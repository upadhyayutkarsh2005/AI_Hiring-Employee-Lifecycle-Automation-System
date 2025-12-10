from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import json

llm = ChatOpenAI(model="gpt-4o-mini")   # or gemini/mistral/ollama


@tool
def screen_resume(jd_output: dict, resume_text: str) -> dict:
    """Screen resume against the job description and return match score + analysis."""

    prompt = f"""
    You are an ATS + HR Resume Screening System.

    Compare the following:

    JOB DESCRIPTION DATA:
    {jd_output}

    RESUME TEXT:
    {resume_text}

    Perform the following tasks:
    - Extract technical & soft skills from resume
    - Match resume skills to JD requirements
    - Identify missing skills
    - Identify strengths & weaknesses
    - Calculate match score (0–100)
    - Suggest decision "Shortlisted" or "Rejected"

    Return output strictly in JSON:
    {{
      "match_score": int,
      "skills_matched": [],
      "skills_missing": [],
      "strengths": [],
      "weaknesses": [],
      "decision": "Shortlisted/Rejected"
    }}
    """

    response = llm.invoke(prompt)
    
    # Extract content from response
    content = response.content
    
    # Remove markdown code blocks if present
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    
    # Parse and return JSON
    return json.loads(content)
