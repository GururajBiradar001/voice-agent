import time
import uuid
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from database import init_db
from stt import transcribe_audio
from tts import synthesize_speech
from agent import run_agent
from memory import get_session, save_session, get_patient_language, save_patient_language
from language import detect_language

load_dotenv(dotenv_path="../.env")

app = FastAPI()

# Initialize DB on startup
@app.on_event("startup")
async def startup():
    init_db()
    print("[SERVER] Database initialized")

# Serve frontend
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
async def root():
   with open("../frontend/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws/{patient_phone}")
async def websocket_endpoint(websocket: WebSocket, patient_phone: str):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    print(f"[WS] New session: {session_id} | Patient: {patient_phone}")

    # Load patient's preferred language from past sessions
    language = get_patient_language(patient_phone)
    messages = get_session(session_id)

    try:
        while True:
            # Receive audio bytes from browser
            audio_data = await websocket.receive_bytes()
            t_start = time.time()

            # Step 1: STT
            t_stt = time.time()
            transcript, detected_lang = await transcribe_audio(audio_data, language)
            stt_ms = (time.time() - t_stt) * 1000

            if not transcript.strip():
                continue

            # Step 2: Detect + update language
            language = detect_language(transcript, detected_lang)
            save_patient_language(patient_phone, language)

            print(f"[PIPELINE] User said: '{transcript}' | Lang: {language}")

            # Step 3: Add to conversation history
            messages.append({"role": "user", "content": transcript})

            # Step 4: Run agent
            t_llm = time.time()
            reply = run_agent(messages, patient_phone, language)
            llm_ms = (time.time() - t_llm) * 1000

            # Step 5: Save reply to history
            messages.append({"role": "assistant", "content": reply})
            save_session(session_id, messages)

            # Step 6: TTS
            t_tts = time.time()
            audio_reply = await synthesize_speech(reply, language)
            tts_ms = (time.time() - t_tts) * 1000

            # Step 7: Total latency log
            total_ms = (time.time() - t_start) * 1000
            print(f"[LATENCY] STT: {stt_ms:.0f}ms | LLM: {llm_ms:.0f}ms | TTS: {tts_ms:.0f}ms | TOTAL: {total_ms:.0f}ms")

            # Step 8: Send audio + transcript back to browser
            await websocket.send_bytes(audio_reply)
            await websocket.send_json({
                "transcript": transcript,
                "reply": reply,
                "language": language,
                "latency": {
                    "stt_ms": round(stt_ms),
                    "llm_ms": round(llm_ms),
                    "tts_ms": round(tts_ms),
                    "total_ms": round(total_ms)
                }
            })

    except WebSocketDisconnect:
        print(f"[WS] Session ended: {session_id}")
        save_session(session_id, messages)