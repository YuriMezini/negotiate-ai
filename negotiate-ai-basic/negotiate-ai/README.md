# NegotiateAI — AI-Powered Salary Negotiation Coach

> **Hackathon Demo v1.0** — Basic Engine (Mock LLM)  
> Every year, $1M+ is left on the table because people don't negotiate. This tool changes that.

## What It Does

1. **Market Value Estimation** — Enter your role, location, experience → get P25/Median/P75 salary range
2. **Negotiation Simulation** — Practice against a simulated hiring manager with real-time coaching
3. **Script Generator** — Get an exact word-for-word script customized to your profile

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Project Structure

```
negotiate-ai/
├── app.py                # Streamlit UI (main entry point)
├── salary_engine.py      # Market value estimation engine
├── negotiation.py        # Negotiation simulation (mock → Gemini)
├── coach.py              # Real-time coaching layer (rule-based → Gemini)
├── script.py             # Final script generator (template → Gemini)
├── data/
│   └── salary_mock.json  # Salary benchmark data
├── requirements.txt
└── README.md
```

## Upgrade Path

| Step | Integration      | Status |
|------|------------------|--------|
| 1    | Basic engine     | ✅ Done |
| 2    | Gemini API       | 🔜 Next |
| 3    | ElevenLabs voice | 🔜     |
| 4    | Solana on-chain  | 🔜     |
| 5    | MongoDB          | 🔜     |

## Current Version: Basic

- **Salary engine**: Static data + location/experience/company multipliers
- **Negotiation**: Scripted multi-turn responses (realistic but not dynamic)
- **Coaching**: Rule-based keyword analysis (detects anchoring, hedging, etc.)
- **Script**: Template-based output with calculated targets

## Next: Gemini Integration

The Gemini upgrade will replace all three AI layers:
- Dynamic hiring manager roleplay (context-aware, pushback, personality)
- LLM-powered coaching (semantic analysis, not just keywords)
- Personalized script generation from full conversation context
