# Real-Time Multilingual Voice AI Agent
### Clinical Appointment Booking System

A real-time voice AI agent that books and manages clinical appointments through natural voice conversations in English, Hindi, and Tamil.

---

## Architecture Overview
```
Browser (Mic) → WebSocket → FastAPI Backend
                                   ↓
                          Deepgram STT (Speech → Text)
                                   ↓
                          GPT-4o Agent (Reasoning + Tool Calling)
                                   ↓
                    ┌──────────────────────────────┐
                    │  Tools:                       │
                    │  - get_available_doctors()    │
                    │  - book_appointment()         │
                    │  - cancel_appointment()       │
                    │  - get_patient_appointments() │
                    └──────────────────────────────┘
                                   ↓
                          OpenAI TTS (Text → Speech)
                                   ↓
                          Browser (Audio Playback)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, WebSockets |
| Frontend | HTML, JavaScript |
| STT | Deepgram Nova-2 |
| LLM | OpenAI GPT-4o |
| TTS | OpenAI TTS-1 |
| Session Memory | Redis (fallback: in-memory) |
| Database | SQLite + SQLAlchemy |

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/voice-agent.git
cd voice-agent
```

### 2. Install dependencies
```bash
cd backend
pip install -r ../requirements.txt
```

### 3. Configure API keys
Create a `.env` file inside the `backend/` folder:
```
OPENAI_API_KEY=your_openai_key_here
DEEPGRAM_API_KEY=your_deepgram_key_here
REDIS_URL=redis://localhost:6379
```

### 4. Run the server
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Open the app
Go to `http://localhost:8000` in Chrome.

---

## Memory Design

### Session Memory (Short-term)
- Stored in **Redis** with 30-minute TTL
- Falls back to in-memory dict if Redis unavailable
- Stores full conversation history per session
- Enables multi-turn conversations with context

### Cross-session Memory (Long-term)
- Stored in **SQLite** via SQLAlchemy
- Persists patient language preference across sessions
- Stores appointment history per patient phone number

---

## Latency Breakdown

Each request is timed and logged:

| Stage | Typical Latency |
|-------|----------------|
| STT (Deepgram) | 300–600ms |
| LLM (GPT-4o) | 800–1500ms |
| TTS (OpenAI) | 300–500ms |
| **Total** | **~1400–2600ms** |

Target was under 450ms — current bottleneck is the LLM step.
Optimization paths: streaming TTS, caching common responses, smaller model for intent detection.

---

## Multilingual Support

- **English** → `en-IN` (Deepgram), GPT-4o responds in English
- **Hindi** → `hi` (Deepgram), GPT-4o responds in Devanagari
- **Tamil** → `ta` (Deepgram), GPT-4o responds in Tamil script
- Language is auto-detected per turn and persisted across sessions

---

## Appointment & Conflict Management

- Double-booking prevention via DB constraint check before confirming
- Past-time slots are not offered
- If requested slot is taken, agent offers next available alternatives
- Full lifecycle: book → reschedule → cancel

---

## Agentic Reasoning

GPT-4o uses tool calling to interact with the scheduling system. Reasoning traces are printed to the server console:
```
[TOOL CALL] get_available_doctors({})
[TOOL RESULT] [{"id": 1, "name": "Dr. Priya Sharma", ...}]
[TOOL CALL] book_appointment({"doctor_id": 1, "slot": "2024-12-20 09:00", ...})
[TOOL RESULT] {"success": true, "appointment_id": 3}
```

---

## Outbound Campaign Mode

The agent supports initiating outbound calls for:
- Appointment reminders
- Follow-up check-ins
- Rescheduling requests

Campaigns are triggered via the `/outbound` API endpoint with patient phone and message template.

---

## Known Limitations

- Latency exceeds 450ms target due to sequential STT→LLM→TTS pipeline
- No real phone call integration (browser-based only)
- Redis must be running locally for session persistence
- TTS voice does not change per language (same OpenAI voice for all)

## Tradeoffs

- Chose SQLite over PostgreSQL for simplicity — easy to swap out
- Chose OpenAI TTS over Deepgram Aura for reliability
- In-memory Redis fallback sacrifices persistence for ease of setup

---

## Bonus Features Implemented

- ✅ Redis-backed memory with TTL
- ✅ Language preference persisted across sessions
- ✅ Reasoning traces visible in server logs
- ✅ Latency measured and logged per request