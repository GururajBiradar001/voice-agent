def detect_language(text: str, deepgram_detected: str = None) -> str:
    """
    Determine language from Deepgram's detection or text heuristics.
    Returns: 'en', 'hi', or 'ta'
    """

    # Trust Deepgram's detection first
    if deepgram_detected:
        if deepgram_detected.startswith("hi"):
            return "hi"
        if deepgram_detected.startswith("ta"):
            return "ta"
        if deepgram_detected.startswith("en"):
            return "en"

    # Fallback: check for script characters in text
    for ch in text:
        if '\u0900' <= ch <= '\u097F':   # Devanagari (Hindi)
            return "hi"
        if '\u0B80' <= ch <= '\u0BFF':   # Tamil script
            return "ta"

    return "en"  # default