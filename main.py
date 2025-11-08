"""
main.py — Unified FastAPI Application

✅ Features:
1. User Management (Add / List users) — via SQLAlchemy
2. Crop Disease Detection — via Google Gemini Vision API
"""

# -------------------- Imports --------------------
import os
import base64
import json
from typing import Optional, List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models import User


# -------------------- Load .env --------------------
load_dotenv()  # ✅ Loads GEMINI_API_KEY from .env file


# -------------------- FastAPI App --------------------
app = FastAPI(title="Agri AI + User API", version="1.0")


# -------------------- DATABASE CONFIG --------------------


# ✅ Auto-create all database tables (like "users") at startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to provide a SQLAlchemy session to endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------- GEMINI CONFIG --------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("❌ Please set GEMINI_API_KEY environment variable before running the app")

# Gemini Vision API endpoint
# GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
# Before (Causing 404 Error):
# GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent")

# --- FIX: Change the model identifier to a current, stable version ---
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
)

# -------------------- MODELS --------------------

# 🧩 Response Models
class Medicine(BaseModel):
    name_en: Optional[str]
    name_hi: Optional[str]
    dose_en: Optional[str]
    dose_hi: Optional[str]
    purpose_en: Optional[str]
    purpose_hi: Optional[str]


class DetectResponse(BaseModel):
    crop_en: Optional[str]
    crop_hi: Optional[str]
    disease_en: Optional[str]
    disease_hi: Optional[str]
    confidence: Optional[float]
    recommendations_en: Optional[str]
    recommendations_hi: Optional[str]
    medicines: Optional[List[Medicine]]
    # raw: Optional[dict]



# ==========================================================
# =============== BASIC TEST ENDPOINTS =====================
# ==========================================================

@app.get("/")
def home():
    """Basic root route to test if FastAPI is working."""
    return {"message": "👋 Hello! FastAPI is running successfully."}


@app.get("/welcome")
def welcome_message():
    """Friendly message endpoint."""
    return {"message": "🚀 Welcome to your combined FastAPI server!"}


# ==========================================================
# =============== USER MANAGEMENT API ======================
# ==========================================================

@app.post("/add_user")
def add_user(name: str, email: str, db: Session = Depends(get_db)):
    """
    ➕ Add a new user to the database.
    - name: str → username
    - email: str → user email
    """
    user = User(name=name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "✅ User added successfully!",
        "user": {"id": user.id, "name": user.name, "email": user.email},
    }


@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    """👥 Fetch all users from the database."""
    users = db.query(User).all()
    return users


# ==========================================================
# ============ CROP DISEASE DETECTION API ==================
# ==========================================================

@app.post("/detect", response_model=DetectResponse)
async def detect_crop_disease(file: UploadFile = File(...)):
    """
    🌾 Detect crop disease using Gemini Vision API.
    Returns bilingual (English + Hindi) response with medicine suggestions.
    """

    # Step 1️⃣ - Validate image
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file received.")

    # Step 2️⃣ - Convert image to Base64
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # Step 3️⃣ - Prompt (English + Hindi + At least 10 Medicines)
    prompt = (
        "You are an agricultural expert AI. Analyze the uploaded crop image carefully and respond "
        "ONLY with valid JSON (no markdown, no extra text). The JSON must contain both English and Hindi fields. "
        "Include detailed disease diagnosis, treatment recommendations, and AT LEAST 10 medicine suggestions "
        "that are commonly used and agriculture-approved in India.\n\n"
        "JSON format:\n"
        "{\n"
        "  \"crop_en\": \"<Crop name in English>\",\n"
        "  \"crop_hi\": \"<फसल का नाम हिंदी में>\",\n"
        "  \"disease_en\": \"<Disease name in English or 'Healthy'>\",\n"
        "  \"disease_hi\": \"<रोग का नाम हिंदी में या 'स्वस्थ'>\",\n"
        "  \"confidence\": <0.0 - 1.0>,\n"
        "  \"recommendations_en\": \"<English treatment and prevention recommendations>\",\n"
        "  \"recommendations_hi\": \"<हिंदी में उपचार और रोकथाम के सुझाव>\",\n"
        "  \"medicines\": [\n"
        "     {\"name_en\": \"<Medicine name in English>\", \"name_hi\": \"<दवा का हिंदी नाम>\", "
        "\"dose_en\": \"<Dose and usage in English>\", \"dose_hi\": \"<मात्रा और उपयोग विधि हिंदी में>\", "
        "\"purpose_en\": \"<Purpose in English>\", \"purpose_hi\": \"<उद्देश्य हिंदी में>\"}\n"
        "  ]\n"
        "}\n\n"
        "⚠️ VERY IMPORTANT: Return at least 10 medicine objects under 'medicines'. "
        "Each should have English + Hindi name, dose, and purpose.\n"
        "⚠️ Output only pure JSON without ```json or markdown code fences.\n"
        "Example:\n"
        "{\n"
        "  \"crop_en\": \"Potato\",\n"
        "  \"crop_hi\": \"आलू\",\n"
        "  \"disease_en\": \"Late Blight\",\n"
        "  \"disease_hi\": \"लेट ब्लाइट\",\n"
        "  \"confidence\": 0.95,\n"
        "  \"recommendations_en\": \"Remove infected leaves and apply fungicides.\",\n"
        "  \"recommendations_hi\": \"संक्रमित पत्तियां हटाएं और फफूंदनाशी का छिड़काव करें।\",\n"
        "  \"medicines\": [\n"
        "     {\"name_en\": \"Mancozeb\", \"name_hi\": \"मैंकोजेब\", \"dose_en\": \"2g/L\", \"dose_hi\": \"2 ग्राम/लीटर\", \"purpose_en\": \"Fungal control\", \"purpose_hi\": \"फफूंद नियंत्रण\"},\n"
        "     {\"name_en\": \"Copper Oxychloride\", \"name_hi\": \"कॉपर ऑक्सी-क्लोराइड\", \"dose_en\": \"2.5g/L\", \"dose_hi\": \"2.5 ग्राम/लीटर\", \"purpose_en\": \"Protectant fungicide\", \"purpose_hi\": \"संरक्षण हेतु फफूंदनाशी\"}\n"
        "  ]\n"
        "}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": file.content_type,
                            "data": image_base64,
                        }
                    },
                ]
            }
        ]
    }

    # Step 5️⃣ - Gemini Headers
    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    }

    # Step 6️⃣ - Call Gemini API
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(GEMINI_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Gemini Error: {response.text}")

    # Step 7️⃣ - Extract Text
    data = response.json()
    print(f'\n\n\nGemini Response:{data}\n\n\n')
    text_resp = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )

    # Step 8️⃣ - Parse JSON Safely
    import re
    try:
        match = re.search(r'```json\s*(\{.*})\s*```', text_resp, re.DOTALL)
        if match:
            clean_json = match.group(1)
        else:
            clean_json = text_resp.strip()
        result = json.loads(clean_json)
    except json.JSONDecodeError:
        result = {"raw_text": text_resp}

    # Step 9️⃣ - Return Structured Response
    return {
        "crop_en": result.get("crop_en"),
        "crop_hi": result.get("crop_hi"),
        "disease_en": result.get("disease_en"),
        "disease_hi": result.get("disease_hi"),
        "confidence": result.get("confidence"),
        "recommendations_en": result.get("recommendations_en"),
        "recommendations_hi": result.get("recommendations_hi"),
        "medicines": result.get("medicines"),
        # "raw": result,
    }



# ==========================================================
# ================== END OF FILE ===========================
