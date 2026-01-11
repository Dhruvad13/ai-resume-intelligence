from fastapi import FastAPI, UploadFile, File, Form
import pickle
from PyPDF2 import PdfReader
import io
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client.ai_interview_coach
history = db.answer_history
from pymongo.errors import ServerSelectionTimeoutError

try:
    client.admin.command("ping")
    print("MongoDB connected successfully")
except ServerSelectionTimeoutError as e:
    print("MongoDB connection failed:", e)


embedder = SentenceTransformer("all-MiniLM-L6-v2")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
    "aws": "What is EC2 and why is it used?",
    "javascript": "Explain event bubbling in JavaScript.",
    "html": "What is semantic HTML and why is it important?",
    "css": "What is the CSS box model?",
}
ideal_answers = {
    "What problem does Docker solve in production systems?":
        "Docker packages applications and their dependencies into containers, ensuring consistent deployment across environments.",
    "Explain indexing in MongoDB.":
        "Indexes in MongoDB improve query performance by reducing the amount of data scanned.",
    "Explain Python decorators with an example.":
        "Decorators modify function behavior without changing its source code."
}


suggestion_bank = {
    "python": "Add a project that demonstrates real Python backend development.",
    "sql": "Mention complex SQL queries and joins you have used.",
    "docker": "Include experience containerizing apps using Docker.",
    "fastapi": "Add REST API project using FastAPI.",
    "mongodb": "Mention schemas and indexing in MongoDB.",
    "react": "Add a frontend project using React.",
    "aws": "Mention any cloud deployment or EC2 usage.",
    "javascript": "Add interactive frontend logic using JavaScript.",
    "html": "Mention clean and semantic HTML structure in projects.",
    "css": "Add responsive layouts using Flexbox or Grid.",
}

job_roles = {
    "backend": ["python","sql","fastapi","docker","mongodb"],
    "frontend": ["react","javascript","css","html"],
    "ml": ["python","pandas","numpy","tensorflow","sklearn"]
}

def evaluate_answer(user_answer, question):
    ideal = ideal_answers.get(question)

    if not ideal:
        return 0.0

    embeddings = embedder.encode([user_answer, ideal])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return round(float(score * 100), 2)



def generate_feedback(answer):
    tips = []
    if "example" not in answer.lower():
        tips.append("Try adding a real-world example.")
    if "how" not in answer.lower():
        tips.append("Explain the working process more clearly.")
    if len(answer.split()) < 25:
        tips.append("Your answer is too short. Add more technical depth.")
    if not tips:
        tips.append("Excellent structured technical explanation.")
    return tips



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
    keywords = ["python","java","sql","flask","fastapi","docker","mongodb","react","node","aws","javascript","html","css"]
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






class AnswerRequest(BaseModel):
    answer: str
    question: str

@app.post("/evaluate")
def evaluate_user_answer(req: AnswerRequest):
    score = evaluate_answer(req.answer, req.question)

    history.insert_one({
        "question": req.question,
        "answer": req.answer,
        "score": score
    })

    return {
        "score": score,
        "feedback": "Excellent understanding" if score > 70 else "Concept needs improvement"
    }

@app.get("/history")
def get_history():
    records = list(history.find({}, {"_id": 0}))
    return records
