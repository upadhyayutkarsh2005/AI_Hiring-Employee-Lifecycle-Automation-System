from fastapi import FastAPI
from api.routes import app as interview_router

app = FastAPI(
    title="AI Hiring - Employee Lifecycle Automation System",
    description="Backend API for AI-powered hiring and employee management",
    version="1.0.0"
)

# Include the interview router
app.mount("/interview", interview_router)

@app.get("/")
async def root():
    return {
        "message": "AI Hiring System API",
        "status": "running",
        "endpoints": {
            "interview_start": "/interview/api/interview/start",
            "interview_answer": "/interview/api/interview/answer"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)