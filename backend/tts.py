import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def synthesize_speech(text: str, language: str = "en") -> bytes:
    """Convert text to speech audio bytes."""

    # Pick voice based on language
    # OpenAI TTS handles multilingual in the same voice
    voice_map = {
        "en": "alloy",
        "hi": "alloy",
        "ta": "alloy"
    }
    voice = voice_map.get(language, "alloy")

    response = await client.audio.speech.create(
        model="tts-1",          # tts-1 is faster, tts-1-hd is higher quality
        voice=voice,
        input=text,
        response_format="mp3"
    )

    audio_bytes = response.content
    print(f"[TTS] Generated {len(audio_bytes)} bytes for: {text[:50]}...")
    return audio_bytes