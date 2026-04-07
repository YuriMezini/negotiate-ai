"""
negotiation.py — Negotiation Simulation Engine
v5: Realistic, adaptive, human-like negotiation with proper acceptance gating.
"""

import re
import random

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


# ─── Intent Detection ─────────────────────────────────────────────────────────

# Phrases that make "accept" conditional — NOT a real acceptance
_CONDITIONAL_PHRASES = [
    "only if", "but if", "but only", "unless", "if you", "if i get",
    "if we", "provided", "as long as", "on condition", "in exchange",
    "in return", "assuming", "given that", "contingent",
]

_PROFANITY = [
    "stupid", "idiot", "dumb", "asshole", "fuck", "shit", "bastard",
    "moron", "jerk", "crap", "damn", "hell", "bitch", "hate you",
    "terrible", "awful", "worst", "useless",
]


def _detect_intent(msg: str) -> str:
    m = msg.lower().strip()

    # Profanity / rude — check early
    if any(w in m for w in _PROFANITY):
        return "profanity"

    # Conditional acceptance (e.g. "I'll accept only if I get 20% more") → NOT acceptance
    is_conditional = any(phrase in m for phrase in _CONDITIONAL_PHRASES)

    # True acceptance — clear, unconditional
    _accept_words = [
        "i accept", "i'll take it", "sounds good", "deal", "works for me",
        "happy with that", "that works", "let's do it", "yes please",
        "i'm in", "you got it", "perfect", "agreed",
    ]
    if not is_conditional and any(w in m for w in _accept_words):
        return "acceptance"

    # "Sounds good" / "great" alone can be acceptance but not when combined with "but"
    if not is_conditional and not any(w in m for w in ["but", "however", "though", "if"]):
        if any(w in m for w in ["yes", "okay", "ok", "great", "sure", "fine"]):
            # Only if message is short (don't trigger on "great, but I need more")
            if len(m.split()) <= 6:
                return "acceptance"

    # Numbers — salary anchor (check before generic push)
    if re.search(r'\$\s*[\d,]+|\b\d[\d,]{3,}\b|\b\d+\s*%\s*(increase|raise|more|higher)', m):
        return "salary_anchor"

    # Work arrangement
    if any(w in m for w in ["remote", "hybrid", "in person", "in-person", "office",
                              "wfh", "work from home", "on-site", "onsite", "flexible work",
                              "commute", "days in", "days at"]):
        return "work_arrangement"

    # Equity
    if any(w in m for w in ["equity", "rsu", "stock", "options", "shares", "vesting", "grant"]):
        return "equity"

    # Signing bonus
    if any(w in m for w in ["signing", "sign-on", "sign on", "one-time", "joining bonus"]):
        return "signing_bonus"

    # PTO
    if any(w in m for w in ["pto", "vacation", "time off", "days off", "holiday",
                              "parental leave", "sick"]):
        return "pto"

    # Benefits
    if any(w in m for w in ["health", "dental", "vision", "insurance", "medical",
                              "401k", "401(k)", "retirement", "hsa", "benefits"]):
        return "benefits"

    # Competing offer
    if any(w in m for w in ["competing", "other offer", "another offer",
                              "counter offer", "different offer", "i have an offer"]):
        return "competing_offer"

    # Market data
    if any(w in m for w in ["market", "glassdoor", "levels.fyi", "levels fyi",
                              "data", "research", "benchmark", "industry", "peer salary"]):
        return "market_data"

    # Salary push (general — no specific number)
    if any(w in m for w in ["higher", "more", "increase", "raise", "better pay",
                              "not enough", "low offer", "underpaid", "worth more",
                              "expect more", "looking for more", "need more", "low salary"]):
        return "salary_push"

    # Stalling
    if any(w in m for w in ["think about", "let me think", "get back", "need time",
                              "not sure yet", "deciding", "considering"]):
        return "stalling"

    # Logistics
    if any(w in m for w in ["start date", "when do i start", "timeline",
                              "onboarding", "first day", "notice period"]):
        return "logistics"

    # Career growth
    if any(w in m for w in ["title", "promotion", "career path", "growth",
                              "level", "advancement", "senior"]):
        return "career_growth"

    return "off_topic"


def _extract_anchor(msg: str) -> int | None:
    """Extract the largest salary-plausible number or compute a % increase."""
    m = msg.lower()
    # Handle "20% increase" style
    pct_match = re.search(r'(\d+)\s*%\s*(increase|raise|more|higher)', m)
    if pct_match:
        return int(pct_match.group(1))  # return as a percentage int, flagged separately

    nums = re.findall(r'[\d,]+', msg.replace(",", ""))
    candidates = [int(n) for n in nums if 40000 < int(n) < 1_000_000]
    return max(candidates) if candidates else None


def _extract_pct_increase(msg: str) -> int | None:
    """Extract percentage increase demand like '20% increase'."""
    m = msg.lower()
    match = re.search(r'(\d+)\s*%\s*(increase|raise|more|higher|bump)', m)
    return int(match.group(1)) if match else None


# ─── NegotiationEngine ────────────────────────────────────────────────────────

class NegotiationEngine:
    """
    Multi-turn salary negotiation.
    - Score-adaptive: HM flexibility driven by live coaching score
    - State-machine: EXPLORING → NEGOTIATING → CONVERGING → CLOSED
    - Anti-repetition: tracks intent history and previous responses
    - Realistic: conditional statements never trigger premature acceptance
    - Handles rude/off-topic inputs gracefully even after deal closes
    """

    def __init__(self, profile: dict, market: dict):
        self.profile = profile
        self.market = market
        self.turn = 0

        self.history: list[dict] = []         # {"role": "hm"|"candidate", "message": str}
        self.gemini_contents: list[dict] = [] # Gemini multi-turn

        self.use_gemini = GEMINI_AVAILABLE
        self.deal_state = "exploring"          # exploring → negotiating → converging → closed
        self.intent_counts: dict[str, int] = {}
        self.topics_discussed: list[str] = []
        self.score_history: list[float] = []
        self.prev_hm_messages: list[str] = [] # for anti-repetition

        offer = profile.get("offer", 95000)
        median = market.get("median", 120000)
        self.initial_offer = offer
        self.adjusted_offer = round(offer + (median - offer) * 0.6)
        self.signing_bonus = int(round(self.adjusted_offer * 0.08, -3))
        self.best_offer_made = False
        self.concession_steps = 0
        # Track whether the last HM message was a yes/no closing question
        # to avoid misreading "yes" (to a side question) as deal acceptance
        self.last_hm_was_closing_question = False

    # ── Score helpers ────────────────────────────────────────────────────────

    @property
    def avg_score(self) -> float:
        return sum(self.score_history) / len(self.score_history) if self.score_history else 5.0

    def _flexibility(self, avg_score: float) -> str:
        if avg_score >= 8:
            return "HIGH"
        if avg_score >= 6:
            return "MEDIUM"
        if avg_score >= 4:
            return "LOW"
        return "MINIMAL"

    def _should_converge(self, avg_score: float) -> bool:
        # Converge after 3 turns with strong negotiating, 4 turns regardless of score
        return (
            (self.turn >= 3 and avg_score >= 7)
            or (self.turn >= 4 and avg_score >= 5)
            or self.turn >= 5
        )

    def _advance_state(self, intent: str, avg_score: float, raw_message: str = "") -> None:
        if self.deal_state == "exploring":
            if intent in ("salary_anchor", "salary_push", "market_data",
                          "competing_offer", "signing_bonus"):
                self.deal_state = "negotiating"
        if self.deal_state == "negotiating" and self._should_converge(avg_score):
            self.deal_state = "converging"
        # Only close on genuine acceptance — guard against ambiguous short "yes"
        # answers to side questions (e.g. "yes" to "do you have a competing offer?")
        if intent == "acceptance":
            is_short_yes = len(raw_message.strip().split()) <= 3
            if is_short_yes and not self.last_hm_was_closing_question:
                pass  # not a deal closure — HM wasn't asking for a yes on the offer
            elif avg_score >= 4 and self.deal_state in ("negotiating", "converging"):
                self.deal_state = "closed"
            elif self.best_offer_made:
                self.deal_state = "closed"

    # ── Gemini integration ───────────────────────────────────────────────────

    def _system_prompt(self) -> str:
        offer = self.initial_offer
        role = self.profile.get("role", "Software Engineer")
        location = self.profile.get("location", "Austin")
        years = self.profile.get("years_exp", 5)
        median = self.market.get("median", 120000)
        max_budget = round(median * 0.95)
        signing_ceil = int(round(offer * 0.12, -3))
        remote = self.profile.get("remote_policy", "Hybrid (2–3 days)")

        return f"""You are Alex, a professional hiring manager at a tech company negotiating a job offer via chat.

=== OFFER CONTEXT ===
Role: {role} | Location: {location} | Experience: {years} yrs
Initial offer: ${offer:,} | Work arrangement: {remote}
Market median (NEVER reveal): ${median:,}
Max base budget: ${max_budget:,} | Max signing bonus: ${signing_ceil:,}

=== HARD RULES ===
1. Read the candidate's EXACT last message before writing anything. Respond to IT.
2. A conditional statement like "I'll accept if I get X" is NOT an acceptance — it's a counter-offer. Treat it as such.
3. If the candidate is rude or uses profanity, respond professionally but firmly: "I'd like to keep this conversation professional." Do NOT celebrate or offer more.
4. NEVER repeat a phrase or argument you already used in this conversation.
5. 2–4 sentences max. Human, warm, direct. No markdown, bullets, asterisks, or bold.
6. NEVER reveal your budget ceiling or internal market data.
7. Only accept the negotiation if the candidate clearly says yes to YOUR offer — not if they make a new demand."""

    def _dynamic_context(self, avg_score: float) -> str:
        flex = self._flexibility(avg_score)
        recent = self.prev_hm_messages[-3:]

        flex_map = {
            "HIGH":    f"Score {avg_score:.1f}/10 — candidate negotiating excellently. Be genuinely open. Can offer up to ${self.adjusted_offer:,} + ${self.signing_bonus:,} signing.",
            "MEDIUM":  f"Score {avg_score:.1f}/10 — good arguments. Make real but incremental concessions.",
            "LOW":     f"Score {avg_score:.1f}/10 — moderate arguments. Push back, ask for specifics first.",
            "MINIMAL": f"Score {avg_score:.1f}/10 — weak arguments. Hold firm. Ask them to clarify their position.",
        }

        converge = ""
        if self.deal_state == "converging" and not self.best_offer_made:
            converge = f"\nMake a concrete best-and-final offer: ${self.adjusted_offer:,} base + ${self.signing_bonus:,} signing bonus."
        elif self.deal_state == "converging" and self.best_offer_made:
            converge = "\nYou already made your best offer. Hold firm, ask them to decide."
        elif self.deal_state == "closed":
            converge = "\nDeal is closed. Confirm warmly, mention offer letter, welcome them."

        prev = "\n".join(f'  "{m[:100]}{"..." if len(m) > 100 else ""}"' for m in recent) or "  (none yet)"

        return (
            f"\n=== TURN {self.turn} | STATE: {self.deal_state.upper()} ===\n"
            f"{flex_map[flex]}{converge}\n"
            f"Topics covered: {', '.join(self.topics_discussed) or 'none'}\n"
            f"Your recent messages (DO NOT repeat these points):\n{prev}\n"
            f"Now respond to the candidate's last message with fresh, specific content."
        )

    def _call_gemini(self, user_message: str, avg_score: float,
                     is_opening: bool = False) -> str | None:
        try:
            contents = list(self.gemini_contents)
            prompt = (
                "Open the negotiation: present the job offer warmly, mention role and salary, end with an open question."
                if is_opening else user_message
            )
            contents.append({"role": "user", "parts": [{"text": prompt}]})

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config={
                    "system_instruction": self._system_prompt() + self._dynamic_context(avg_score),
                    "temperature": 0.78,
                    "max_output_tokens": 280,
                },
            )

            reply = re.sub(r'\*+', '', response.text.strip()).strip()
            if not reply:
                return None

            if str(self.adjusted_offer) in reply:
                self.best_offer_made = True

            self.gemini_contents.append({"role": "user", "parts": [{"text": prompt}]})
            self.gemini_contents.append({"role": "model", "parts": [{"text": reply}]})
            return reply

        except Exception as e:
            print(f"[NegotiationEngine] Gemini error: {e}")
            return None

    # ── Scripted fallback — intent-based, count-aware, score-adaptive ─────────

    def _scripted_response(self, user_message: str, avg_score: float,
                           intent: str, prev_count: int) -> str:
        """
        prev_count: how many times this intent was seen BEFORE this message (0 = first time).
        """
        offer = self.initial_offer
        role = self.profile.get("role", "this role")
        remote = self.profile.get("remote_policy", "Hybrid (2–3 days)")
        flex = self._flexibility(avg_score)

        # ── Profanity / rude ─────────────────────────────────────────────────
        if intent == "profanity":
            responses = [
                "I'd like to keep this conversation professional — I'm here to work through the offer details with you, and I'd appreciate if we could do that respectfully.",
                "Let's keep things professional. I'm genuinely trying to find a package that works for you, and I'd like to continue that conversation constructively.",
                "I understand negotiations can be stressful, but I need us to keep this respectful. Happy to continue when you're ready.",
            ]
            return random.choice(responses)

        # ── Deal closed — handle all post-close inputs realistically ─────────
        if self.deal_state == "closed":
            if intent == "profanity":
                return "I'd prefer to keep things professional even after agreeing on the offer. I'll send the paperwork shortly."
            if intent in ("salary_push", "salary_anchor"):
                return (
                    "We already reached an agreement — I wouldn't be able to reopen the conversation at this stage. "
                    "The offer letter will be with you within 24 hours."
                )
            if intent == "off_topic":
                return (
                    "We're all set! I'll get the paperwork drafted and over to you shortly. "
                    "Reach out if you have any questions before then."
                )
            # Generic post-close
            return "We're confirmed — offer letter coming within 24 hours. Really looking forward to having you on the team."

        # ── Converging — make best offer if not yet made ─────────────────────
        if self.deal_state == "converging" and intent not in ("acceptance", "profanity"):
            if not self.best_offer_made:
                self.best_offer_made = True
                return (
                    f"I've pushed hard internally and here's the best I can get approved: "
                    f"${self.adjusted_offer:,} base with a ${self.signing_bonus:,} signing bonus. "
                    f"That's a strong jump from where we started, and it's our ceiling. "
                    f"Does that work for you?"
                )
            else:
                return (
                    f"I've already put our best offer on the table — ${self.adjusted_offer:,} base "
                    f"plus ${self.signing_bonus:,} signing. I'm not going to be able to move beyond that. "
                    f"What's your call?"
                )

        # ── True acceptance ───────────────────────────────────────────────────
        if intent == "acceptance":
            # Don't close if the offer is just the initial one and score is very low
            if not self.best_offer_made and avg_score < 5:
                return (
                    f"I'm glad you're interested! Just to confirm — you're happy with the full package "
                    f"as presented: ${offer:,} base and our standard benefits. Is that a yes?"
                )
            self.deal_state = "closed"
            return random.choice([
                f"Excellent — I'm really glad we could land on something that works! "
                f"I'll get the updated offer letter drafted and over to you within 24 hours. Welcome aboard!",
                f"That's great news — the team is going to be thrilled. "
                f"I'll have the formal offer letter to you by tomorrow. Welcome to the team!",
            ])

        # ── Work arrangement ─────────────────────────────────────────────────
        if intent == "work_arrangement":
            pct = _extract_pct_increase(user_message)
            has_salary_ask = any(w in user_message.lower() for w in
                                  ["raise", "more", "increase", "higher", "salary"])

            if has_salary_ask:
                # They asked about BOTH — address both
                if prev_count == 0:
                    return (
                        f"Those are two separate asks, so let me take them one at a time. "
                        f"On work arrangement, we offer {remote} for this role. "
                        f"On salary — our ${offer:,} was benchmarked carefully, but I'm open to hearing what number you have in mind."
                    )
                return (
                    f"On the work arrangement, {remote} is what we've confirmed for this role. "
                    f"On the compensation side — you mentioned wanting more. "
                    f"What specific number would make you comfortable signing?"
                )
            if prev_count == 0:
                return (
                    f"For this {role} role we offer {remote}. "
                    f"That's been a real positive for the team's productivity. "
                    f"On the compensation side, is there anything about the ${offer:,} base you'd like to discuss?"
                )
            return (
                f"To be clear, the arrangement is {remote} — that's set for this role. "
                f"Is flexibility on that a dealbreaker for you, or is compensation the bigger question?"
            )

        # ── Conditional counter-offer (e.g. "I accept if I get 20% more") ────
        # This gets caught as salary_anchor or salary_push, so we handle the
        # "conditional" framing in those branches below.

        # ── Salary anchor ─────────────────────────────────────────────────────
        if intent == "salary_anchor":
            pct = _extract_pct_increase(user_message)
            anchor = _extract_anchor(user_message)

            # Percentage-based demand (e.g. "I want 20% increase")
            if pct and pct > 0:
                target = round(offer * (1 + pct / 100))
                achievable = target <= self.adjusted_offer * 1.05
                if achievable and (flex in ("HIGH", "MEDIUM") or prev_count >= 1):
                    if not self.best_offer_made:
                        self.best_offer_made = True
                        return (
                            f"A {pct}% increase is meaningful, and I hear you. "
                            f"I went back to the team — best I can get to is ${self.adjusted_offer:,} base "
                            f"plus a ${self.signing_bonus:,} signing bonus. "
                            f"That's roughly {round((self.adjusted_offer - offer) / offer * 100)}% up from the initial offer. Does that work?"
                        )
                    return (
                        f"I've already put our best forward: ${self.adjusted_offer:,} base + ${self.signing_bonus:,} signing. "
                        f"I can't go to a full {pct}% bump, but this gets you meaningfully closer. "
                        f"What's your thinking?"
                    )
                return (
                    f"A {pct}% increase would put you at ${target:,}, which is a significant jump. "
                    f"I'd need a strong case to bring that back to comp. "
                    f"What's driving that number specifically — market data, another offer?"
                )

            # Dollar-anchored demand
            if anchor and anchor > offer:
                gap = anchor - offer
                pct_gap = round(gap / offer * 100)
                if flex == "HIGH" and prev_count >= 1:
                    self.best_offer_made = True
                    return (
                        f"I've gone back to the team on your ${anchor:,} ask. "
                        f"I can get to ${self.adjusted_offer:,} base plus a ${self.signing_bonus:,} signing bonus — "
                        f"that's my ceiling. Does that bridge the gap?"
                    )
                if pct_gap > 25:
                    return (
                        f"${anchor:,} is a {pct_gap}% jump from our ${offer:,} — that's a stretch. "
                        f"I'd need a real justification to take that to the comp committee. "
                        f"Are you working from a competing offer or specific market data?"
                    )
                return (
                    f"You're at ${anchor:,}, we're at ${offer:,} — I see the gap. "
                    f"Let me see what room I have. To make the strongest case internally: "
                    f"what's the single most important thing for you right now?"
                )
            return (
                f"Our ${offer:,} was carefully benchmarked for this role and location. "
                f"What specific number would make you ready to move forward?"
            )

        # ── Salary push (no number) ────────────────────────────────────────────
        if intent == "salary_push":
            if prev_count == 0:
                return (
                    f"I hear you — you're looking for more, and I want to find something that works. "
                    f"Our ${offer:,} reflects careful market benchmarking, but I'm not saying there's zero room. "
                    f"What specific number do you have in mind?"
                )
            if prev_count == 1 and flex in ("MEDIUM", "HIGH"):
                return (
                    f"I pushed on our end. There's some room to move, but I need to know your target "
                    f"to make the right case internally. Give me a number and I'll see what I can do."
                )
            if prev_count >= 2 or flex == "HIGH":
                self.best_offer_made = True
                return (
                    f"I've gone to bat for you internally. Best I can get approved: "
                    f"${self.adjusted_offer:,} base plus a ${self.signing_bonus:,} signing bonus. "
                    f"That's a real move from where we started — does that get us to a yes?"
                )
            return (
                f"I understand you're looking for more flexibility on the comp. "
                f"To move this forward, I really do need a specific target number. "
                f"What would make you sign today?"
            )

        # ── Equity ────────────────────────────────────────────────────────────
        if intent == "equity":
            if prev_count == 0:
                return (
                    f"Equity is part of the total package — we offer RSU grants on a 4-year vesting schedule. "
                    f"The exact grant amount is formalized in the offer letter based on level and role. "
                    f"Is equity a major factor for you, or is base salary the main focus?"
                )
            return (
                f"On equity — the RSU grant depends on where we land on the base, since the two are linked. "
                f"Once we agree on comp, the equity gets calculated and included. "
                f"What would you want the RSU grant to look like?"
            )

        # ── Signing bonus ──────────────────────────────────────────────────────
        if intent == "signing_bonus":
            if flex in ("HIGH", "MEDIUM") or prev_count >= 1:
                self.best_offer_made = True
                return (
                    f"I can get a ${self.signing_bonus:,} signing bonus approved — "
                    f"that's a one-time payment on your first paycheck alongside the ${offer:,} base. "
                    f"Does adding that to the package get us to a yes?"
                )
            return (
                f"Signing bonuses aren't always in the initial letter, but there's some flexibility there. "
                f"What number were you thinking, and how does that sit alongside the ${offer:,} base?"
            )

        # ── PTO ────────────────────────────────────────────────────────────────
        if intent == "pto":
            if prev_count == 0:
                return (
                    f"PTO is generous — we have a competitive policy and a culture that actually encourages people to use it. "
                    f"Is there a specific number of days you're looking for, or is it the flexibility that matters more?"
                )
            return (
                f"I can connect you with HR after we finalize the offer to go through the PTO specifics in detail. "
                f"In the meantime, what would you say is your biggest outstanding concern on the compensation side?"
            )

        # ── Benefits ────────────────────────────────────────────────────────────
        if intent == "benefits":
            if prev_count == 0:
                return (
                    f"Our benefits are strong — comprehensive health, dental and vision for you and your family, "
                    f"plus a 401(k) with company match. Is there a specific benefit you'd like more detail on?"
                )
            return (
                f"Happy to have HR walk you through the full benefits breakdown once we align on the offer. "
                f"Is there one particular benefit that's a dealbreaker if it's not in place?"
            )

        # ── Competing offer ────────────────────────────────────────────────────
        if intent == "competing_offer":
            if prev_count == 0:
                return (
                    f"I appreciate you being upfront — it shows you're taking this seriously. "
                    f"Can you tell me what that package looks like? "
                    f"I want to see if we can compete for you, because we genuinely want you here."
                )
            if flex in ("HIGH", "MEDIUM"):
                self.best_offer_made = True
                return (
                    f"Given the competing offer, I pushed hard on our end. "
                    f"Best I can do: ${self.adjusted_offer:,} base + ${self.signing_bonus:,} signing. "
                    f"I think that's a strong counter — what does the math look like for you?"
                )
            return (
                f"I hear you on the competing offer. Can you tell me what specifically they're offering? "
                f"I want to make an informed case internally before going back to the comp team."
            )

        # ── Market data ─────────────────────────────────────────────────────────
        if intent == "market_data":
            if prev_count == 0:
                return (
                    f"I appreciate the research — that's a sign of a prepared candidate. "
                    f"Our ${offer:,} is benchmarked for {role} at your level in {self.profile.get('location', 'this market')}. "
                    f"What specific data are you referencing? That helps me have a better conversation with our comp team."
                )
            return (
                f"I've gone back to the team with the market data you mentioned. "
                f"There's some movement available — but to make the right ask, "
                f"what total compensation number are you targeting?"
            )

        # ── Stalling ───────────────────────────────────────────────────────────
        if intent == "stalling":
            return (
                f"Totally fair — this is a big decision and you should feel confident about it. "
                f"We do have a few candidates in the final stage, so ideally we'd like an answer by end of week. "
                f"Is there a specific question I can answer right now to help you move forward?"
            )

        # ── Logistics ──────────────────────────────────────────────────────────
        if intent == "logistics":
            return (
                f"On timing, we're flexible — we can work around your current notice period, no pressure. "
                f"Once we nail down the package, we'll sort the start date together. "
                f"Speaking of which, any remaining questions on the offer?"
            )

        # ── Career growth ───────────────────────────────────────────────────────
        if intent == "career_growth":
            return (
                f"Career trajectory is something we take seriously here. "
                f"This {role} role has a clear growth path with semi-annual performance reviews "
                f"and comp adjustments tied directly to impact. "
                f"What specifically are you hoping to see — scope expansion, title progression, or speed to the next level?"
            )

        # ── Off-topic ───────────────────────────────────────────────────────────
        off_topic_responses = [
            f"Ha — let's make sure we get you the best deal first! "
            f"Is there something specific about the ${offer:,} offer, the benefits, or the total package you'd like to revisit?",

            f"I want to make sure we're using our time well here. "
            f"On the offer side — what's the one thing that would make you feel confident saying yes?",

            f"Good question, though let's make sure we wrap up the offer details first. "
            f"What's the biggest outstanding thing for you right now?",
        ]
        return random.choice(off_topic_responses)

    # ── Public API ────────────────────────────────────────────────────────────

    def get_opening(self) -> str:
        response = None
        if self.use_gemini:
            response = self._call_gemini("", avg_score=5.0, is_opening=True)

        if not response:
            offer = self.initial_offer
            role = self.profile.get("role", "this role")
            response = random.choice([
                f"Thanks for your time today — the whole team has been excited about this. "
                f"I'm happy to officially extend an offer for {role} with a base salary of ${offer:,}. "
                f"We believe it reflects your experience and the market well. What are your initial thoughts?",

                f"Great to connect — we've been really impressed and we'd love to have you as our {role}. "
                f"The offer we're putting forward is ${offer:,} base, plus our full benefits package. "
                f"Any first reactions?",

                f"The whole team is hoping you'll say yes! We're extending an offer for {role} at ${offer:,} base. "
                f"We think it's a strong and competitive package. "
                f"What questions do you have about what's on the table?",
            ])

        self.history.append({"role": "hm", "message": response})
        self.prev_hm_messages.append(response)
        self.turn = 1
        return response

    def respond(self, user_message: str, avg_score: float = 5.0) -> str:
        """
        Generate a realistic, context-aware HM response.
        avg_score: rolling average coaching score (1–10) passed from the coach.
        """
        self.history.append({"role": "candidate", "message": user_message})
        self.turn += 1
        self.score_history.append(avg_score)

        # Detect intent and track BEFORE making response (prev_count = seen count before this message)
        intent = _detect_intent(user_message)
        prev_count = self.intent_counts.get(intent, 0)
        self.intent_counts[intent] = prev_count + 1
        if intent not in self.topics_discussed:
            self.topics_discussed.append(intent)

        # Advance state machine (pass raw message so short "yes" can be gated)
        self._advance_state(intent, avg_score, raw_message=user_message)

        response = None

        if self.use_gemini:
            response = self._call_gemini(user_message, avg_score)

        if not response:
            response = self._scripted_response(user_message, avg_score, intent, prev_count)

        if str(self.adjusted_offer) in response:
            self.best_offer_made = True

        # Track whether THIS response is asking the candidate to yes/no the deal
        _closing_cues = [
            "does that work", "is that a yes", "does that get us",
            "what's your call", "what do you say", "shall we", "do we have a deal",
            "can we close", "are you in", "ready to sign", "what do you think",
            "take it or leave", "your decision", "can we move forward",
        ]
        self.last_hm_was_closing_question = any(c in response.lower() for c in _closing_cues)

        self.history.append({"role": "hm", "message": response})
        self.prev_hm_messages.append(response)
        return response

    @property
    def engine_type(self) -> str:
        return "gemini" if self.use_gemini else "scripted"

    def get_transcript(self) -> str:
        lines = []
        for entry in self.history:
            speaker = "Hiring Manager" if entry["role"] == "hm" else "You"
            lines.append(f"**{speaker}:** {entry['message']}")
        return "\n\n".join(lines)

    def get_history_for_llm(self) -> list:
        messages = []
        for entry in self.history:
            role = "model" if entry["role"] == "hm" else "user"
            messages.append({"role": role, "content": entry["message"]})
        return messages
