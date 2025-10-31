from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
from .database import init_db, save_plan, save_feedback, get_dashboard_stats
from .ocr_processor import extract_from_image
from .ai_planner import get_ai_plan
from .feedback_handler import analyze_sentiment


init_db()

app = FastAPI(
    title="MVp - Medication Victory Plan",
    description="OCR + AI Food Timing + Patient Sentiment",
    version="4.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # CHANGE THIS IN PROD
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/ocr")
async def ocr_upload(file: UploadFile = File(...)):
    allowed = ["image/png", "image/jpeg", "application/pdf"]
    if file.content_type not in allowed:
        raise HTTPException(400, "Only PNG, JPG, PDF allowed")
    
    content = await file.read()
    result = extract_from_image(content, file.content_type)
    
    return {
        "parsed": {
            "name": result["name"],
            "dose": result["dose"]
        }
        # NO raw_text → PII safe
    }


@app.post("/api/plan")
async def get_plan(
    name: str = Form(...),
    dose: str = Form(...),
    frequency: str = Form(...),
    source: Optional[str] = Form("manual")
):
    """Generate AI plan with timing + replacements"""
    med_key = f"{name} {dose}".lower()
    advice = get_ai_plan(name, dose, frequency)
    
    # Save to SQLite
    save_plan(name, dose, frequency, advice, source)
    
    return {
        "med": med_key,
        "advice": advice,
        "source": source
    }


@app.post("/api/feedback")
async def submit_feedback(
    med: str = Form(...),
    feedback: str = Form(...),
    source: Optional[str] = Form("web")
):
    """Analyze feedback using AventIQ-AI model"""
    sentiment = analyze_sentiment(feedback)
    save_feedback(med.lower(), feedback, sentiment, source)
    
    return {"sentiment": sentiment}


@app.get("/api/dashboard")
async def dashboard():
    """Return feedback stats for frontend visualization"""
    return get_dashboard_stats()

# ====================== PUBLIC API (v1) ======================
@app.post("/v1/medication/plan")
async def v1_plan(name: str, dose: str, frequency: str, source: str = "api"):
    return await get_plan(name=name, dose=dose, frequency=frequency, source=source)

@app.post("/v1/medication/feedback")
async def v1_feedback(med: str, feedback: str, source: str = "api"):
    return await submit_feedback(med=med, feedback=feedback, source=source)

@app.get("/v1/dashboard")
async def v1_dashboard():
    return await dashboard()


