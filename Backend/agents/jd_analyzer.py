from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json

load_dotenv() 

llm = ChatOpenAI(model="gpt-4o-mini")


@tool
def analyze_job_description(jd: str) -> dict:
    """Analyze the job description and return structured JSON."""
    prompt = f"""
    Analyze the job description and extract:

    1. Job Role
    2. Required Skills
    3. Nice-to-have Skills
    4. Experience Level
    5. Responsibilities
    6. Interview Questions
    7. Scoring Rubric out of 100
    
    JD:
    {jd}

    Return only valid JSON without markdown code blocks.
    """
    response = llm.invoke(prompt)
    
    # Extract content from response
    content = response.content
    
    # Remove markdown code blocks if present
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    
    # Parse JSON
    return json.loads(content)