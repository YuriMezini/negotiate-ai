"""
coach.py — Real-Time Negotiation Coaching Layer
v3: Calibrated Gemini agent with realistic low/high scores + pre-screening.
"""

import json
import random
import re

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


# ─── Dismissive / profane / garbage patterns ───
DISMISSIVE_EXACT = {
    "yes", "no", "ok", "okay", "sure", "fine", "whatever", "idk",
    "i don't care", "i dont care", "don't care", "dont care",
    "doesn't matter", "doesnt matter", "i give up", "just give me the money",
    "anything", "i'll take it", "deal", "accepted", "agreed", "k", "y", "n",
    "sounds good", "looks good", "that's fine", "that works",
}

PROFANITY = {
    "fuck", "shit", "damn", "hell", "crap", "ass", "bitch",
    "wtf", "stfu", "idgaf",
}

TACTICAL_ADVICE = [
    "Use anchoring: state a specific number backed by market data before they set the frame.",
    "Practice the power of silence — after making your ask, stop talking. Let them respond.",
    "Never say 'I think' or 'maybe' — use definitive language: 'Based on my research...'",
    "Frame everything as mutual value: 'I want to find a number that reflects the value I'll deliver.'",
    "Always negotiate total comp, not just base: signing bonus, equity, PTO, remote flexibility.",
    "Use the 'I need to think about it' technique — never accept on the spot, even if it's great.",
    "If they push back, ask 'What would it take to get to $X?' — make them solve the problem.",
    "Don't reveal your current salary or minimum — keep the focus on market value for the role.",
    "End every counter with a question, not a statement. It keeps dialogue open.",
    "Mirror their language: if they say 'competitive', say 'I agree we should aim for competitive.'",
]


def _pre_classify(message: str) -> dict | None:
    """
    Fast pre-screen for obviously bad input before hitting the LLM.
    Returns a complete result dict if the input is clearly garbage/dismissive,
    or None if it should be sent to Gemini for full analysis.
    """
    stripped = message.strip().lower()
    words = stripped.split()
    word_count = len(words)

    # ── Profanity ──
    if any(w in PROFANITY for w in words):
        return {
            "power": 1,
            "mistakes": [
                "Profanity is an instant disqualifier — it destroys your credibility immediately.",
                "No hiring manager will engage professionally after offensive language.",
            ],
            "strengths": [],
            "improved": (
                "I appreciate the offer. After reviewing, I'd like to discuss the base compensation — "
                "my research shows the market rate for this role is higher. Can we explore that?"
            ),
            "advice": "Professionalism is non-negotiable. Stay calm, composed, and data-driven — that's where your real leverage lives.",
        }

    # ── Exact dismissive match ──
    if stripped in DISMISSIVE_EXACT or (word_count <= 3 and stripped in DISMISSIVE_EXACT):
        return {
            "power": 1,
            "mistakes": [
                f"'{message.strip()}' is not a negotiation — it's a surrender.",
                "One-word or dismissive responses forfeit all your leverage instantly.",
                "You gave away your position without getting anything in return.",
            ],
            "strengths": [],
            "improved": (
                "Thank you for the offer. I've done some research on market compensation for this role "
                "and I'd like to discuss the base salary. Based on my experience and the market data, "
                "I was targeting something closer to the median range. Is there flexibility there?"
            ),
            "advice": "Every response is a move. Say something specific — a number, a data point, or a question. Silence or one-word answers hand all the power to the other side.",
        }

    # ── Very short / low-effort (≤4 words, not dismissive but not useful) ──
    if word_count <= 4:
        return {
            "power": 2,
            "mistakes": [
                f"Only {word_count} words — far too short to negotiate effectively.",
                "Short vague responses signal you have no leverage or preparation.",
            ],
            "strengths": [],
            "improved": (
                "I appreciate the offer. Based on my research into market rates for this role, "
                "I was expecting something closer to the market median. "
                "Can we discuss adjusting the base compensation?"
            ),
            "advice": "A negotiation response needs at least: (1) acknowledge the offer, (2) make a specific counter, (3) justify it with data or value. Aim for 3-5 sentences minimum.",
        }

    # ── Full LLM analysis needed ──
    return None


def _gemini_analyze(message: str, profile: dict, market: dict) -> dict:
    """
    Calibrated Gemini coaching analysis.
    The prompt is designed to produce realistic low scores (1-3) for weak inputs.
    """
    try:
        offer = profile.get("offer", 0)
        median = market.get("median", 0)
        p75 = market.get("p75", 0)
        word_count = len(message.split())

        prompt = f"""You are a brutally honest, expert salary negotiation coach. Your job is to give REALISTIC scores — most candidates negotiate poorly and deserve low scores.

CANDIDATE PROFILE:
- Role: {profile.get('role', 'Software Engineer')}
- Location: {profile.get('location', 'Unknown')}
- Experience: {profile.get('years_exp', 0)} years
- Current offer: ${offer:,}
- Market P25: ${market.get('p25', 0):,} | Median: ${median:,} | P75: ${p75:,}
- The candidate is LEAVING ${max(0, median - offer):,}/year on the table vs market median

CANDIDATE'S MESSAGE ({word_count} words):
"{message}"

STRICT SCORING RUBRIC — be calibrated, not generous:
• 1: Meaningless or destructive response — one/two words, "ok/sure/fine/yes/no/deal/whatever", accepting without countering, profanity, off-topic, dismissive ("I don't care")
• 2: Passive acceptance — no counter-offer, no leverage used, just acknowledging the offer with mild interest
• 3: Weak attempt — vague interest in more money but no specific number, too apologetic, uncertain language ("I think maybe...", "I'm not sure but...")
• 4: Below average — counter-offer exists but undershoots market median, no data cited, too eager
• 5: Average — has a counter but it's weak: either too low, hedged, or not justified
• 6: Decent — counter near or at median, some justification, reasonably confident tone
• 7: Good — specific number at or above median, data-backed, professional, keeps options open
• 8: Strong — excellent anchoring, specific data cited (Glassdoor/Levels.fyi), value framing, strategic
• 9: Expert — perfect tactical execution, anchors high, justifies with multiple data points, ends with open question
• 10: Masterclass — textbook salary negotiation, would work in any real negotiation

CALIBRATION EXAMPLES:
- "yes" → power: 1
- "ok, sounds good" → power: 1
- "I don't care" → power: 1  
- "I need more money" → power: 2
- "can you do a bit better?" → power: 3
- "I was hoping for a little more, maybe $5k?" → power: 4
- "I'd like $110k" (below median of ${median:,}) → power: 4
- "Based on the market, ${median:,} seems fair" → power: 6
- "My research shows ${p75:,} for this role. Given my X years, I'm targeting ${median:,}" → power: 8

Respond with ONLY valid JSON (no markdown, no backticks):
{{
    "power": <integer 1-10, be strict and realistic>,
    "mistakes": [<list of 0-3 SHORT specific strings about what went wrong in THIS message>],
    "strengths": [<list of 0-3 SHORT specific strings about what was done well in THIS message>],
    "improved": "<a rewrite of THEIR message using best tactics — specific numbers, market data, confident tone — 3-4 sentences>",
    "advice": "<one concrete thing they must do differently in their NEXT response — be specific, reference their actual words>"
}}

IMPORTANT:
- mistakes and strengths must be about THIS specific message, not generic advice
- improved must reference their actual situation (${offer:,} offer, ${median:,} median, {profile.get('role','this role')})
- If the message is vague or non-committal, power MUST be 3 or below
- Do NOT be encouraging just to be nice — honesty helps them improve"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config={
                "temperature": 0.2,
                "max_output_tokens": 600,
            },
        )

        raw = response.text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)

        # Validate fields
        assert "power" in result and isinstance(result["power"], (int, float))
        assert "improved" in result and isinstance(result["improved"], str)
        assert "advice" in result and isinstance(result["advice"], str)

        result["power"] = max(1, min(10, int(result["power"])))
        result.setdefault("mistakes", [])
        result.setdefault("strengths", [])

        # Sanity check: very short messages should never score above 4
        if len(message.split()) <= 6 and result["power"] > 4:
            result["power"] = 4
            result["mistakes"].insert(0, f"Response too short ({len(message.split())} words) — not enough to negotiate effectively")

        return result

    except Exception as e:
        print(f"Gemini coaching error: {e}")
        return None


def _rule_based_analyze(message: str, profile: dict, market: dict) -> dict:
    """
    Fallback rule-based analysis — calibrated baseline based on message quality.
    """
    msg_lower = message.lower().strip()
    words = msg_lower.split()
    word_count = len(words)
    mistakes = []
    strengths = []

    # ── Baseline from message length / effort ──
    if word_count <= 4:
        power = 2
        mistakes.append(f"Only {word_count} words — far too short to negotiate effectively")
    elif word_count <= 10:
        power = 3
    elif word_count <= 25:
        power = 4
    else:
        power = 5

    # ── Strong signals ──
    strong_signals = {
        "market_data": ["market data", "research shows", "benchmark", "industry standard",
                        "glassdoor", "levels.fyi", "payscale", "comparable roles", "survey"],
        "value_framing": ["my experience", "impact", "revenue", "saved", "led", "delivered",
                          "built", "managed", "grew", "reduced costs", "improved", "value I bring"],
        "non_commitment": ["i'd like to explore", "open to discussing", "want to understand",
                           "could we consider", "what flexibility", "is there room"],
        "specific_ask": ["$", "base of", "looking for", "targeting", "expecting"],
    }
    for tactic, keywords in strong_signals.items():
        if any(kw in msg_lower for kw in keywords):
            power += 1
            if tactic == "market_data":
                strengths.append("Good use of market data to justify your position")
            elif tactic == "value_framing":
                strengths.append("Framing your value proposition — effective tactic")
            elif tactic == "non_commitment":
                strengths.append("Non-committal phrasing keeps options open")
            elif tactic == "specific_ask":
                strengths.append("Making a specific ask — concrete numbers are powerful")

    # ── Weak signals (heavier penalties than before) ──
    weak_signals = {
        "over_eager": ["i'll take it", "sounds great", "that works", "i accept",
                       "perfect", "love it", "no problem", "fine with me", "i'm happy with"],
        "apologetic": ["sorry", "i hate to ask", "i know this is awkward",
                       "don't want to be difficult", "i feel bad", "forgive me", "apolog"],
        "uncertain": ["i guess", "maybe", "kind of", "not sure", "i think",
                      "possibly", "might be", "i was hoping", "perhaps"],
        "underselling": ["i'd be happy with anything", "whatever you think is fair",
                         "just grateful", "any increase", "even a little"],
        "vague": ["a bit more", "a little more", "slightly higher", "some more",
                  "a small raise", "a bit higher", "just more"],
    }
    for weakness, keywords in weak_signals.items():
        if any(kw in msg_lower for kw in keywords):
            power -= 2  # Heavier penalty: -2 instead of -1
            if weakness == "over_eager":
                mistakes.append("Accepting too quickly surrenders all your leverage")
            elif weakness == "apologetic":
                mistakes.append("Apologetic language signals weakness and undermines your position")
            elif weakness == "uncertain":
                mistakes.append("Hedging words ('I think', 'maybe') destroy negotiating confidence")
            elif weakness == "underselling":
                mistakes.append("Gratitude-based framing is the weakest negotiating position")
            elif weakness == "vague":
                mistakes.append("'A bit more' is not a negotiation — give a specific dollar number")

    # ── Too long / rambling ──
    if word_count > 100:
        power -= 1
        mistakes.append("Too long and rambling — concise messages land harder. Aim for 2-4 sentences.")

    # ── Number analysis ──
    median = market.get("median", 0)
    offer = profile.get("offer", 0)
    numbers = re.findall(r'\$?([\d,]+)\s*k?', message)
    found_number = False
    for num_str in numbers:
        try:
            num = int(num_str.replace(",", ""))
            if num < 1000:
                num *= 1000
            if 30000 <= num <= 1000000:
                found_number = True
                if num >= median:
                    power += 2
                    strengths.append(f"Anchoring at ${num:,} — at or above market median (${median:,})")
                elif num > offer:
                    power += 1
                    if num < median:
                        mistakes.append(f"Your ask of ${num:,} is below the market median (${median:,}) — aim higher")
        except ValueError:
            pass

    if not found_number and word_count > 5:
        power -= 1
        mistakes.append(f"No specific dollar amount mentioned — always anchor with a number (target: ${median:,}+)")

    power = max(1, min(10, power))

    # ── Improved version ──
    improved = (
        f"Thank you for the offer. I've done extensive research on compensation for {profile.get('role', 'this role')} "
        f"roles in {profile.get('location', 'this market')}, and the market median is ${median:,} with top performers "
        f"earning up to ${market.get('p75', 0):,}. Given my {profile.get('years_exp', '')} years of experience "
        f"and the value I'll bring, I'm targeting a base of ${median:,}. Is there flexibility to get there?"
    )

    return {
        "power": power,
        "mistakes": mistakes[:3],
        "strengths": strengths[:3],
        "improved": improved,
        "advice": random.choice(TACTICAL_ADVICE),
    }


def analyze_message(message: str, profile: dict, market: dict) -> dict:
    """
    Analyze a negotiation message with a 3-layer approach:
    1. Pre-screen for obvious garbage/dismissive input (instant low score)
    2. Gemini for calibrated semantic analysis
    3. Rule-based fallback
    """
    # Layer 1: Pre-screen
    pre = _pre_classify(message)
    if pre is not None:
        return pre

    # Layer 2: Gemini
    if GEMINI_AVAILABLE:
        result = _gemini_analyze(message, profile, market)
        if result is not None:
            return result

    # Layer 3: Rule-based fallback
    return _rule_based_analyze(message, profile, market)
