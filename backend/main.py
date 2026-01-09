from fastapi import FastAPI, UploadFile, File
import pickle
from PyPDF2 import PdfReader
import io
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Form
import spacy

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
nlp = spacy.load("en_core_web_sm")
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

question_bank = {
    "python": "Explain Python decorators with an example.",
    "sql": "What is normalization? Explain different normal forms.",
    "docker": "What problem does Docker solve in production systems?",
    "fastapi": "How is FastAPI faster than Flask?",
    "mongodb": "Explain indexing in MongoDB.",
    "react": "What is virtual DOM?",
    "aws": "What is EC2 and why is it used?"
}
suggestion_bank = {
    "python": "Add a project that demonstrates real Python backend development.",
    "sql": "Mention complex SQL queries and joins you have used.",
    "docker": "Include experience containerizing apps using Docker.",
    "fastapi": "Add REST API project using FastAPI.",
    "mongodb": "Mention schemas and indexing in MongoDB.",
    "react": "Add a frontend project using React.",
    "aws": "Mention any cloud deployment or EC2 usage."
}
job_roles = {
    "backend": ["python","sql","fastapi","docker","mongodb"],
    "frontend": ["react","javascript","css","html"],
    "ml": ["python","pandas","numpy","tensorflow","sklearn"]
}

def extract_text(upload_file: UploadFile):
    pdf_bytes = upload_file.file.read()
    reader = PdfReader(io.BytesIO(pdf_bytes))

    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content
    return text
def extract_skills(text):
    keywords = ["python","java","sql","flask","fastapi","docker","mongodb","react","node","aws"]
    text = text.lower()
    return list(set([skill for skill in keywords if skill in text]))


@app.post("/predict")
async def predict_resume(role: str = Form(...), file: UploadFile = File(...)):


    text = extract_text(file)

    if not text.strip():
        return {"error": "Could not extract text from PDF"}

    vec = vectorizer.transform([text])
    prob = model.predict_proba(vec)[0][1]

    skills = extract_skills(text)

    required_skills = job_roles.get(role.lower(), job_roles["backend"])
    missing = list(set(required_skills) - set(skills))

    questions = [question_bank[s] for s in missing if s in question_bank]
    suggestions = [suggestion_bank[s] for s in missing if s in suggestion_bank]

    return {
    "selected": bool(prob > 0.5),
    "score": float(round(prob * 100, 2)),
    "skills_found": skills,
    "missing_skills": missing,
    "interview_questions": questions,
    "resume_suggestions": suggestions
    }

