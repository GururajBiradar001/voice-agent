import os
import httpx
from dotenv import load_dotenv

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

async def transcribe_audio(audio_bytes: bytes, language: str = "en") -> str:
    """Send audio to Deepgram and get transcript back."""

    # Map our language codes to Deepgram's
    lang_map = {
        "en": "en-IN",   # English (India)
        "hi": "hi",      # Hindi
        "ta": "ta",      # Tamil
    }
    dg_language = lang_map.get(language, "en-IN")

    url = "https://api.deepgram.com/v1/listen"
    params = {
        "language": dg_language,
        "model": "nova-2",
        "smart_format": "true",
        "detect_language": "true"   # auto-detect too
    }
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/webm"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, params=params, headers=headers, content=audio_bytes)
        data = response.json()

    try:
        transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
        detected_lang = data["results"]["channels"][0]["detected_language"]
        print(f"[STT] Transcript: {transcript} | Detected lang: {detected_lang}")
        return transcript, detected_lang
    except Exception as e:
        print(f"[STT ERROR] {e} | Response: {data}")
        return "", language