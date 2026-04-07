"""
script.py — Negotiation Script Generator
v2: Gemini-powered personalized scripts with template fallback.
"""

import json

# ─── Try to load Gemini ───
try:
    from google import genai
    from config import GEMINI_API_KEY, GEMINI_MODEL
    if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
        client = genai.Client(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        client = None
        GEMINI_AVAILABLE = False
except ImportError:
    client = None
    GEMINI_AVAILABLE = False


def _gemini_generate(profile: dict, market: dict, transcript: str) -> dict:
    """Use Gemini to generate a personalized negotiation script."""
    try:
        offer = profile.get("offer", 0)
        median = market.get("median", 0)
        p75 = market.get("p75", 0)
        target = round(median * 1.05, -3) if (median - offer) / median > 0.2 else median

        prompt = f"""You are an elite salary negotiation coach. Generate a complete, personalized negotiation script.

CANDIDATE PROFILE:
- Role: {profile.get('role', 'Software Engineer')}
- Location: {profile.get('location', 'Unknown')}
- Experience: {profile.get('years_exp', 0)} years
- Company tier: {profile.get('company_tier', 'Unknown')}
- Current offer: ${offer:,}
- Market P25: ${market.get('p25', 0):,}
- Market Median: ${median:,}
- Market P75: ${p75:,}

{"NEGOTIATION TRANSCRIPT FROM PRACTICE:" + chr(10) + transcript if transcript else "No practice session yet."}

Generate a JSON response with ONLY these fields (no markdown, no backticks):
{{
    "opening": "<exact word-for-word script for the opening statement, 3-5 sentences, confident but collaborative tone, reference specific market data>",
    "target": {int(target)},
    "target_justification": "<2-3 sentences explaining why this target is justified, citing market data and experience>",
    "fallback": "<exact word-for-word fallback script if they push back, 2-3 sentences, pivot to total comp — signing bonus, equity, review timeline>",
    "fallback_target": {int(round((target + offer) / 2, -3))},
    "signing_bonus": {int(round(target * 0.08, -3))},
    "closing": "<exact closing statement, 1-2 sentences, express enthusiasm while anchoring the ask>",
    "confidence": <number 0-100 indicating likelihood of success>,
    "expected_outcome": "<3-4 sentences describing best case, likely case, and worst case outcomes with specific dollar amounts>",
    "tips": [
        "<tip 1: specific to this candidate's situation>",
        "<tip 2: tactical advice for the conversation>",
        "<tip 3: what to do if they say no>",
        "<tip 4: body language / tone advice>",
        "<tip 5: follow-up strategy>"
    ]
}}

IMPORTANT RULES:
- The opening script must sound natural, not robotic
- Include specific dollar amounts throughout
- Reference the candidate's experience and market data
- If there was a practice transcript, learn from the mistakes made there
- The fallback should pivot to total compensation, not just accept less
- Tips should be actionable and specific, not generic"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config={
                "temperature": 0.4,
                "max_output_tokens": 1000,
            },
        )

        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        result = json.loads(raw)

        # Validate required fields exist
        required = ["opening", "target", "fallback", "closing", "confidence", "tips"]
        for field in required:
            assert field in result, f"Missing field: {field}"

        # Ensure numeric fields
        result["target"] = int(result.get("target", target))
        result["fallback_target"] = int(result.get("fallback_target", round((target + offer) / 2, -3)))
        result["signing_bonus"] = int(result.get("signing_bonus", round(target * 0.08, -3)))
        result["confidence"] = max(0, min(100, int(result.get("confidence", 70))))

        return result

    except Exception as e:
        print(f"Gemini script generation error: {e}")
        return None  # Triggers fallback


def _template_generate(profile: dict, market: dict, transcript: str) -> dict:
    """Fallback template-based script generation."""
    offer = profile.get("offer", 0)
    role = profile.get("role", "this role")
    location = profile.get("location", "your area")
    years = profile.get("years_exp", 0)
    median = market.get("median", 0)
    p25 = market.get("p25", 0)
    p75 = market.get("p75", 0)
    gap_pct = round((median - offer) / median * 100) if median > 0 else 0

    if gap_pct > 20:
        target = round(median * 1.05, -3)
        confidence = 85
    elif gap_pct > 10:
        target = median
        confidence = 75
    elif gap_pct > 0:
        target = round((median + offer) / 2 + (median - offer) * 0.3, -3)
        confidence = 65
    else:
        target = round(offer * 1.05, -3)
        confidence = 50

    fallback_target = round((target + offer) / 2, -3)
    signing_bonus = round(target * 0.08, -3)

    return {
        "opening": (
            f"Thank you for extending this offer — I'm genuinely excited about joining the team as {role}. "
            f"I've done thorough research on compensation for this role in {location}, and based on "
            f"market benchmarks from multiple sources, the range for {role} with {years} years of "
            f"experience is ${median:,} to ${p75:,}. "
            f"Given my background and the impact I expect to make, I was hoping we could discuss "
            f"a base salary closer to ${target:,}. Is there flexibility on the base compensation?"
        ),
        "target": target,
        "target_justification": (
            f"The target of ${target:,} is justified by the market median of ${median:,} for {role} "
            f"roles in {location}, adjusted for your {years} years of experience. The P75 is ${p75:,}, "
            f"making this ask well within reasonable range."
        ),
        "fallback": (
            f"I understand there are budget considerations. Would ${fallback_target:,} base work if we "
            f"supplement with a ${signing_bonus:,} signing bonus? I'm also open to discussing an "
            f"accelerated performance review at 6 months with a clear path to the target range."
        ),
        "fallback_target": fallback_target,
        "signing_bonus": signing_bonus,
        "closing": (
            f"I want to make this work because I'm excited about the role and the team. "
            f"If we can land at ${target:,} — or close to it with a signing bonus — I'm ready to sign. "
            f"What can we do to make this happen?"
        ),
        "confidence": confidence,
        "expected_outcome": (
            f"Best case: ${target:,} base + ${signing_bonus:,} signing bonus. "
            f"Likely case: ${fallback_target:,} base + some signing bonus or accelerated review. "
            f"Worst case: They hold at ${offer:,} — you have leverage data to negotiate at review time."
        ),
        "tips": [
            "Deliver the opening with a calm, confident tone — not aggressive, not apologetic.",
            "After stating your number, stop talking. Let them respond first.",
            "If they say 'that's outside our range,' ask 'What IS the range?' — gather intel.",
            "Never accept on the first call. Always say 'I'd like to sleep on it.'",
            "If they won't budge on base, negotiate: signing bonus, equity, PTO, remote, title.",
            f"Your walk-away number should be ${fallback_target:,}. Below this, seriously reconsider.",
        ],
    }


def generate_script(profile: dict, market: dict, transcript: str = "") -> dict:
    """
    Generate a complete negotiation script.
    Uses Gemini for personalized output, falls back to templates.
    """
    # Try Gemini first
    if GEMINI_AVAILABLE:
        result = _gemini_generate(profile, market, transcript)
        if result is not None:
            return result

    # Fallback to templates
    return _template_generate(profile, market, transcript)
