"""
config.py — All API keys and configuration in one place.
"""
import os

# ─── Gemini ───
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBmbNJViNYy2ZTNxW_Hv1kWIZVV6DBpWH4")
GEMINI_MODEL = "gemini-2.0-flash"

# ─── ElevenLabs ───
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_5dc63c4fe42b72724edbf2bbc7a2c5b46b7ed4d43861efa3")
ELEVENLABS_VOICE_ID = "XrExE9yKIg1WjnnlVkGX"  # Matilda — Knowledgable, Professional (premade, free tier)

# ─── MongoDB ───
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb+srv://malekzribi:malekzribi@cluster0.ntbjlvr.mongodb.net/?appName=Cluster0")
MONGODB_DB_NAME = "negotiate_ai"

# ─── Solana ───
SOLANA_RPC_URL = "https://api.devnet.solana.com"  # Free devnet, no key needed
