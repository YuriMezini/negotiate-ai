"""
voice_engine.py — ElevenLabs Voice Integration
Text-to-speech (HM responses) + Speech-to-text (user mic input).
"""

import io

try:
    from elevenlabs import ElevenLabs
    from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

    if ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != "PASTE_YOUR_ELEVENLABS_KEY_HERE":
        el_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        VOICE_AVAILABLE = True
    else:
        el_client = None
        VOICE_AVAILABLE = False
except ImportError:
    el_client = None
    VOICE_AVAILABLE = False


def text_to_speech(text: str) -> tuple[bytes | None, str | None]:
    """
    Convert text to MP3 audio bytes using ElevenLabs TTS.
    Returns (audio_bytes, None) on success, (None, error_message) on failure.
    """
    if not VOICE_AVAILABLE:
        return None, "ElevenLabs not configured"
    try:
        audio_generator = el_client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            text=text,
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128",
        )
        return b"".join(chunk for chunk in audio_generator), None
    except Exception as e:
        msg = str(e)
        # Extract the human-readable part from ElevenLabs error body
        if "missing_permissions" in msg:
            friendly = "API key is missing TTS permission — go to elevenlabs.io → API Keys → enable Text to Speech"
        elif "401" in msg or "unauthorized" in msg.lower():
            friendly = "Invalid API key — check elevenlabs.io"
        elif "quota" in msg.lower() or "429" in msg:
            friendly = "ElevenLabs quota exceeded"
        else:
            friendly = f"ElevenLabs error: {msg[:120]}"
        print(f"ElevenLabs TTS error: {msg}")
        return None, friendly


def speech_to_text(audio_data: bytes, mime_type: str = "audio/webm") -> tuple[str | None, str | None]:
    """
    Transcribe audio bytes to text using ElevenLabs Scribe STT.
    Returns (transcript, None) on success, (None, error_message) on failure.
    """
    if not VOICE_AVAILABLE:
        return None, "ElevenLabs not configured"
    if not audio_data:
        return None, "No audio data received"
    try:
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "recording.webm"
        result = el_client.speech_to_text.convert(
            file=("recording.webm", audio_file, mime_type),
            model_id="scribe_v1",
        )
        text = (result.text or "").strip()
        return (text, None) if text else (None, "No speech detected")
    except Exception as e:
        msg = str(e)
        if "missing_permissions" in msg:
            friendly = "API key is missing STT permission — enable Speech to Text on elevenlabs.io"
        elif "401" in msg:
            friendly = "Invalid API key"
        else:
            friendly = f"ElevenLabs STT error: {msg[:120]}"
        print(f"ElevenLabs STT error: {msg}")
        return None, friendly


def is_available() -> bool:
    """Check if voice engine is configured and available."""
    return VOICE_AVAILABLE


def autoplay_audio_html(audio_bytes: bytes) -> str:
    """
    Returns an HTML snippet with a hidden <audio autoplay> element.
    Inject via st.markdown(..., unsafe_allow_html=True) for silent auto-play
    with no visible player widget.
    """
    import base64
    b64 = base64.b64encode(audio_bytes).decode()
    return (
        f'<audio autoplay style="display:none;position:absolute;">'
        f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3">'
        f'</audio>'
    )
