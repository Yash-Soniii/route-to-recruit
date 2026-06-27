from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google import genai

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

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
resend.api_key = os.getenv("RESEND_API_KEY")

@app.post("/extract-skills")
async def extract_skills(file: UploadFile = File(...)):
    contents = await file.read()
    text = ""
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"Extract only technical skills, tools, technologies from this resume. Return comma separated list only:\n\n{text}"
    )
    skills = [s.strip() for s in response.text.split(",")]
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