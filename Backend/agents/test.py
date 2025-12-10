from graph import app
import json

result = app.invoke({
    "jd_text": """
    Falkome AI is looking for a passionate MERN Stack Developer to join our core team and help us build scalable, intelligent web solutions. This is a full-time, remote position perfect for a developer with 2-3 years of hands-on experience in the MERN ecosystem.
    
    What we're looking for:
    - Proficiency in MongoDB, Express.js, React.js, and Node.js
    - Solid understanding of RESTful APIs
    - Experience with version control systems like Git
    - Familiarity with cloud platforms (AWS, Heroku) is a plus
    - Strong problem-solving skills and attention to detail
    
    Responsibilities:
    - Develop and maintain web applications using the MERN stack
    - Collaborate with cross-functional teams to define, design, and ship new features
    - Optimize applications for maximum speed and scalability
    - Participate in code reviews and contribute to team knowledge sharing
    - Stay updated with emerging technologies and industry trends
    """
    
    
    ,"resume_filepath": "/Users/utkarshupadhyay/Computer Science/Project-final_year/AI_Hiring-Employee-Lifecycle-Automation-System/utils/Gurusewak_Resume.pdf"
    
})

print(json.dumps(result["jd_output"], indent=2))
print(json.dumps(result["resume_output"], indent=2))
