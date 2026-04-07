# negotiate-ai
AI-powered salary negotiation assistant
# 🤝 NegotiateAI — AI-Powered Salary Negotiation Assistant

> **Stop leaving money on the table.** NegotiateAI gives everyone access to the same knowledge and confidence as an expert negotiator — in seconds.

---

## 💡 The Problem

Only **30–40%** of job candidates negotiate their salary offers. Those who do earn **5–10% more** on average — which can add up to over **$100,000** in lost lifetime earnings for those who don't. People don't negotiate because they don't know their market value, don't know what to say, and fear making a mistake. Meanwhile, companies come to the table with better data and more experience.

**NegotiateAI levels the playing field.**

---

## 🚀 What It Does

NegotiateAI is an AI-powered salary negotiation assistant. You provide your job offer — it gives you three things instantly:

| Feature | Description |
|---|---|
| 📊 **Fair Salary Range** | Real market data for your role, location, and experience |
| 🧠 **Negotiation Strategy** | A clear, personalized plan to approach the conversation |
| 💬 **Exact Words to Say** | A ready-to-send counteroffer message, written for you |

### Example

> A candidate receives an offer for a **Data Analyst role in Michigan** at **$70,000**.
> - NegotiateAI identifies the fair range: **$78,000 – $85,000**
> - Recommends a counteroffer at: **$82,000**
> - Generates the message:
> *"Thank you for the offer. I'm very excited about the role. Based on my experience and market data, I was expecting something closer to $82,000."*

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | [Streamlit](https://streamlit.io/) |
| AI Engine | Google Gemini (`google-genai`) |
| Voice | ElevenLabs |
| Charts | Plotly |
| Database | MongoDB (`pymongo`) |
| Blockchain | Solders (Solana) |
| HTTP | Requests |

---

## ⚙️ Project Structure

```
negotiate-ai/
├── app.py              # Main Streamlit application
├── negotiation.py      # Core negotiation logic
├── coach.py            # AI coaching engine
├── salary_engine.py    # Salary range analysis
├── voice_engine.py     # Voice interaction (ElevenLabs)
├── blockchain.py       # Blockchain integration
├── database.py         # MongoDB connection & queries
├── config.py           # App configuration
├── script.py           # Utility scripts
├── requirements.txt    # Python dependencies
└── data/               # Data assets
```

---

## 🏁 Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up environment variables

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_google_gemini_key
ELEVENLABS_API_KEY=your_elevenlabs_key
MONGODB_URI=your_mongodb_connection_string
```

### 3. Run the app

```bash
streamlit run app.py
```

---

## 🔭 Vision

- **Today:** AI-powered salary negotiation
- **Tomorrow:** A full AI career agent — helping you at every stage of your professional journey

---

## 👥 Team

| Name | Role |
|---|---|
| **Sara Mezuri** | Team Member |
| **Malek Zibri ** | Team Member |
| **Marouene Addhoum ** | Team Member |

---

## 📄 License

This project was built as part of a hackathon / academic project. All rights reserved by the NegotiateAI team.
