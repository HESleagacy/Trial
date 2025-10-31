from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for JSON requests
class PlanRequest(BaseModel):
    name: str
    dose: str
    frequency: str
    source: Optional[str] = "manual"

class FeedbackRequest(BaseModel):
    med: str
    feedback: str
    source: Optional[str] = "web"

@app.post("/api/ocr")
async def ocr_upload(file: UploadFile = File(...)):
    allowed = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]
    if file.content_type not in allowed:
        raise HTTPException(400, "Only PNG, JPG, PDF allowed")
    
    content = await file.read()
    result = extract_from_image(content, file.content_type)
    
    return {
        "parsed": {
            "name": result["name"],
            "dose": result["dose"]
        }
    }


@app.post("/api/plan")
async def get_plan(request: PlanRequest):
    """Generate AI plan with timing + replacements"""
    med_key = f"{request.name} {request.dose}".lower()
    advice = get_ai_plan(request.name, request.dose, request.frequency)
    
    # Save to SQLite
    save_plan(request.name, request.dose, request.frequency, advice, request.source)
    
    return {
        "med": med_key,
        "advice": advice,
        "source": request.source
    }


@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Analyze feedback using AventIQ-AI model"""
    sentiment = analyze_sentiment(request.feedback)
    save_feedback(request.med.lower(), request.feedback, sentiment, request.source)
    
    return {"sentiment": sentiment}


@app.get("/api/dashboard")
async def dashboard():
    """Return feedback stats for frontend visualization"""
    return get_dashboard_stats()

# ====================== PUBLIC API (v1) ======================
@app.post("/v1/medication/plan")
async def v1_plan(name: str = Form(...), dose: str = Form(...), frequency: str = Form(...), source: str = Form("api")):
    request = PlanRequest(name=name, dose=dose, frequency=frequency, source=source)
    return await get_plan(request)

@app.post("/v1/medication/feedback")
async def v1_feedback(med: str = Form(...), feedback: str = Form(...), source: str = Form("api")):
    request = FeedbackRequest(med=med, feedback=feedback, source=source)
    return await submit_feedback(request)

@app.get("/v1/dashboard")
async def v1_dashboard():
    return await dashboard()

