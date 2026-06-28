from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import pdfplumber
import resend
import io
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
resend.api_key = os.getenv("RESEND_API_KEY")

@app.post("/extract-skills")
async def extract_skills(file: UploadFile = File(...)):
    contents = await file.read()
    text = ""
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user",
            "content": f"Extract only technical skills, tools, technologies from this resume. Return comma separated list only, no explanation:\n\n{text}"
        }]
    )
    skills = [s.strip() for s in response.choices[0].message.content.split(",")]
    return {"skills": skills}

@app.post("/send-alert")
async def send_alert(data: dict):
    resend.Emails.send({
        "from": os.getenv("SENDER_EMAIL"),
        "to": data["email"],
        "subject": "ResumeRoute — New Job Match Found!",
        "html": f"<h2>Hi {data['name']},</h2><p>You have a <b>{data['score']}% match</b> with <b>{data['job_title']}</b> at <b>{data['company']}</b>.</p><a href='{data['job_url']}'>View Job</a>"
    })
    return {"status": "sent"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/extract-skills-text")
async def extract_skills_text(data: dict):
    text = data.get("text", "")
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user",
            "content": f"Extract only technical skills, tools, technologies from this resume. Return comma separated list only, no explanation:\n\n{text[:8000]}"
        }]
    )
    skills = [s.strip() for s in response.choices[0].message.content.split(",")]
    return {"skills": skills}