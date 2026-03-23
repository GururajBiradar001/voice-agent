import json
import os
import redis
from database import SessionLocal, Patient
from dotenv import load_dotenv

load_dotenv()

# Redis for session memory (fast, temporary)
try:
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    r.ping()
    REDIS_AVAILABLE = True
    print("[MEMORY] Redis connected")
except:
    REDIS_AVAILABLE = False
    print("[MEMORY] Redis not available, using in-memory fallback")
    _fallback = {}

SESSION_TTL = 1800  # 30 minutes

def get_session(session_id: str) -> list:
    """Get conversation history for current session."""
    if REDIS_AVAILABLE:
        data = r.get(f"session:{session_id}")
        return json.loads(data) if data else []
    return _fallback.get(session_id, [])

def save_session(session_id: str, messages: list):
    """Save conversation history."""
    if REDIS_AVAILABLE:
        r.setex(f"session:{session_id}", SESSION_TTL, json.dumps(messages))
    else:
        _fallback[session_id] = messages

def get_patient_language(phone: str) -> str:
    """Get preferred language from past sessions."""
    db = SessionLocal()
    patient = db.query(Patient).filter(Patient.phone == phone).first()
    db.close()
    return patient.preferred_language if patient else "en"

def save_patient_language(phone: str, language: str):
    """Persist detected language preference."""
    db = SessionLocal()
    patient = db.query(Patient).filter(Patient.phone == phone).first()
    if patient:
        patient.preferred_language = language
        db.commit()
    db.close()