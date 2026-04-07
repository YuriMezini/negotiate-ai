"""
app.py — NegotiateAI: AI-Powered Salary Negotiation Coach
Main Streamlit application.

Run: streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go

from salary_engine import (
    estimate_market_value,
    analyze_offer,
    get_available_roles,
    LOCATIONS,
    COMPANY_TIERS,
)
from negotiation import NegotiationEngine
from coach import analyze_message
from script import generate_script
from voice_engine import text_to_speech, speech_to_text, autoplay_audio_html, is_available as voice_available
from database import save_session, get_recent_sessions, save_outcome, get_aggregate_stats, is_available as db_available
from blockchain import create_salary_proof, get_network_status, is_available as solana_available


# ─── Page Config ───
st.set_page_config(
    page_title="NegotiateAI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* ─── GLOBAL RESET ─── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
div[data-testid="stToolbar"] {display: none;}
div[data-testid="stDecoration"] {display: none;}

.stApp {
    background: #020617;
    color: #E2E8F0;
    font-family: 'DM Sans', sans-serif;
}

/* ─── SIDEBAR ─── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #020617 100%);
    border-right: 1px solid #1E293B;
}
section[data-testid="stSidebar"] .stMarkdown p {
    font-family: 'DM Sans', sans-serif;
}

/* ─── INPUT FIELDS ─── */
.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #0F172A !important;
    color: #E2E8F0 !important;
    border: 1px solid #1E293B !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stSelectbox > div > div:hover,
.stNumberInput > div > div > input:hover,
.stTextInput > div > div > input:hover { border-color: #10B981 !important; }
.stSelectbox > div > div:focus-within,
.stNumberInput > div > div > input:focus,
.stTextInput > div > div > input:focus {
    border-color: #10B981 !important;
    box-shadow: 0 0 0 2px rgba(16,185,129,0.15) !important;
}
.stSelectbox [data-baseweb="popover"] { background-color: #0F172A !important; border: 1px solid #1E293B !important; }
.stSelectbox [role="option"] { background-color: #0F172A !important; color: #E2E8F0 !important; }
.stSelectbox [role="option"]:hover { background-color: #1E293B !important; }

/* ─── SLIDER ─── */
.stSlider > div > div > div > div { background-color: #10B981 !important; }
.stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"] { color: #64748B !important; }

/* ─── BUTTONS ─── */
.stButton > button {
    background: linear-gradient(135deg, #10B981, #059669) !important;
    color: #022C22 !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.5px;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 0 15px rgba(16,185,129,0.2);
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 0 25px rgba(16,185,129,0.4) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ─── CHAT INPUT ─── */
.stChatInput { background-color: #0F172A !important; border: 1px solid #1E293B !important; border-radius: 12px !important; }
.stChatInput textarea { background-color: #0F172A !important; color: #E2E8F0 !important; font-family: 'DM Sans', sans-serif !important; }

/* ─── EXPANDER ─── */
div[data-testid="stExpander"] { background: #0F172A; border: 1px solid #1E293B; border-radius: 12px; overflow: hidden; }
div[data-testid="stExpander"] summary { font-family: 'DM Sans', sans-serif; color: #94A3B8; }

/* ─── DIVIDERS ─── */
hr { border-color: #1E293B !important; }

/* ─── SCROLLBAR ─── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #020617; }
::-webkit-scrollbar-thumb { background: #1E293B; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #334155; }

/* ─── LABELS ─── */
.stSelectbox label, .stNumberInput label, .stTextInput label,
.stSlider label, .stTextArea label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important;
    color: #10B981 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}

/* ─── METRIC CARDS ─── */
.metric-card {
    background: linear-gradient(135deg, #0F172A, #1E293B);
    border: 1px solid #1E293B;
    border-radius: 14px;
    padding: 22px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
.metric-label { font-family: 'DM Mono', monospace; font-size: 0.7rem; color: #64748B; letter-spacing: 1.5px; text-transform: uppercase; }
.metric-value { font-family: 'DM Mono', monospace; font-size: 1.6rem; font-weight: 600; margin-top: 4px; }

/* ─── CHAT BUBBLES ─── */
.chat-hm {
    background: linear-gradient(135deg, #1E293B, #0F172A);
    border: 1px solid #1E293B;
    border-radius: 16px 16px 16px 4px;
    padding: 14px 18px;
    margin: 10px 0;
    max-width: 85%;
    font-size: 0.9rem;
    line-height: 1.7;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
.chat-user {
    background: linear-gradient(135deg, #10B981, #059669);
    color: #022C22;
    border-radius: 16px 16px 4px 16px;
    padding: 14px 18px;
    margin: 10px 0 10px auto;
    max-width: 85%;
    font-size: 0.9rem;
    line-height: 1.7;
    text-align: right;
    box-shadow: 0 2px 8px rgba(16,185,129,0.2);
}
.chat-label { font-family: 'DM Mono', monospace; font-size: 0.6rem; opacity: 0.5; letter-spacing: 1.5px; margin-bottom: 6px; text-transform: uppercase; }

/* ─── COACH CARDS ─── */
.coach-card {
    background: linear-gradient(135deg, #0F172A, #020617);
    border: 1px solid #1E293B;
    border-radius: 14px;
    padding: 18px;
    margin: 10px 0;
    transition: border-color 0.2s;
}
.coach-card:hover { border-color: #334155; }

/* ─── SCRIPT BLOCKS ─── */
.script-block {
    background: linear-gradient(135deg, #0F172A, #020617);
    border: 1px solid #1E293B;
    border-left: 3px solid #10B981;
    border-radius: 12px;
    padding: 22px;
    margin: 14px 0;
    font-size: 0.9rem;
    line-height: 1.9;
}

/* ─── VERDICT CARDS ─── */
.verdict-card { border-radius: 16px; padding: 28px; margin: 20px 0; position: relative; overflow: hidden; }
.verdict-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.verdict-underpaid { background: linear-gradient(135deg, rgba(239,68,68,0.1), rgba(239,68,68,0.02)); border: 1px solid rgba(239,68,68,0.2); }
.verdict-underpaid::before { background: linear-gradient(90deg, #EF4444, #F59E0B); }
.verdict-competitive { background: linear-gradient(135deg, rgba(16,185,129,0.1), rgba(16,185,129,0.02)); border: 1px solid rgba(16,185,129,0.2); }
.verdict-competitive::before { background: linear-gradient(90deg, #10B981, #3B82F6); }

/* ─── AMBIENT GLOW ─── */
.glow-container { position: relative; }
.glow-container::before {
    content: '';
    position: fixed;
    top: -200px; right: -200px;
    width: 500px; height: 500px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(16,185,129,0.06), transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* ─── PROGRESS GLOW ANIMATION ─── */
@keyframes progressGlow {
    0%, 100% { box-shadow: 0 0 5px rgba(16,185,129,0.3); }
    50% { box-shadow: 0 0 15px rgba(16,185,129,0.6); }
}
.progress-active { animation: progressGlow 2s ease-in-out infinite; }
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ───
if "step" not in st.session_state:
    st.session_state.step = "profile"
if "profile" not in st.session_state:
    st.session_state.profile = {}
if "market" not in st.session_state:
    st.session_state.market = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "negotiation" not in st.session_state:
    st.session_state.negotiation = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "coaching_results" not in st.session_state:
    st.session_state.coaching_results = []
if "script_data" not in st.session_state:
    st.session_state.script_data = None
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None
if "session_saved" not in st.session_state:
    st.session_state.session_saved = False
if "blockchain_proof" not in st.session_state:
    st.session_state.blockchain_proof = None
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = 0
if "queued_voice_input" not in st.session_state:
    st.session_state.queued_voice_input = None
if "auto_play_audio" not in st.session_state:
    st.session_state.auto_play_audio = None


# ─── Header ───
st.markdown('<div class="glow-container">', unsafe_allow_html=True)
col_logo, col_badge = st.columns([4, 1])
with col_logo:
    st.markdown('''
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:6px;">
        <svg width="40" height="40" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="32" height="32" rx="9" fill="#10B981"/>
            <path d="M8 22L16 10L24 22" stroke="#022C22" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 18H20" stroke="#022C22" stroke-width="2.5" stroke-linecap="round"/>
        </svg>
        <span style="font-family:Space Grotesk,sans-serif;font-size:1.9rem;font-weight:700;color:#E2E8F0;letter-spacing:1px;">
            NEGOTIATE<span style="color:#10B981;">AI</span>
        </span>
    </div>
    <p style="font-family:DM Sans,sans-serif;color:#64748B;font-size:0.9rem;margin:0 0 0 54px;">
        AI-powered salary negotiation coach — know your worth, practice your pitch, get your script.
    </p>
    ''', unsafe_allow_html=True)
with col_badge:
    st.markdown('''
    <div style="text-align:right;margin-top:10px;">
        <span style="font-family:DM Mono,monospace;font-size:0.6rem;color:#022C22;background:#10B981;
        padding:5px 12px;border-radius:20px;letter-spacing:1px;font-weight:700;">v3.0 FULL STACK</span>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('<hr style="border-color:#1E293B;margin:20px 0;">', unsafe_allow_html=True)

# ─── Progress indicator ───
steps = ["Profile", "Market Analysis", "Negotiation Sim", "Your Script"]
step_map = {"profile": 0, "market": 1, "negotiate": 2, "script": 3}
current = step_map.get(st.session_state.step, 0)

progress_html = '<div style="display:flex;gap:6px;margin:4px 0 28px 0;">'
for i, label in enumerate(steps):
    is_active = i <= current
    is_current = i == current
    bar_bg = "linear-gradient(90deg,#10B981,#059669)" if is_active else "#1E293B"
    text_color = "#10B981" if is_active else "#475569"
    glow_class = "progress-active" if is_current else ""
    dot = "●" if is_active else "○"
    progress_html += f'''
    <div style="flex:1;text-align:center;">
        <div class="{glow_class}" style="height:4px;background:{bar_bg};border-radius:3px;margin-bottom:8px;"></div>
        <span style="font-family:DM Mono,monospace;font-size:0.6rem;color:{text_color};letter-spacing:1.5px;">
            {dot} {label.upper()}
        </span>
    </div>'''
progress_html += '</div>'
st.markdown(progress_html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════
#  STEP 1: PROFILE INPUT
# ═══════════════════════════════════════════════
if st.session_state.step == "profile":
    st.markdown("### 📋 Enter Your Offer Details")
    st.markdown(
        '<p style="color:#64748B;font-size:0.88rem;margin:-8px 0 16px 0;">'
        'Fill in what\'s in your offer letter. Only the core fields are required — add optional details for a richer compensation breakdown.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('''
    <div style="background:linear-gradient(135deg,rgba(16,185,129,0.05),rgba(59,130,246,0.05));
    border:1px solid #1E293B;border-radius:14px;padding:20px;margin:0 0 24px 0;
    display:flex;justify-content:space-around;text-align:center;">
        <div>
            <p style="font-family:DM Mono,monospace;font-size:1.4rem;color:#10B981;font-weight:700;margin:0;">73%</p>
            <p style="font-family:DM Sans,sans-serif;font-size:0.7rem;color:#64748B;margin:4px 0 0 0;">of people never negotiate</p>
        </div>
        <div style="width:1px;background:#1E293B;"></div>
        <div>
            <p style="font-family:DM Mono,monospace;font-size:1.4rem;color:#F59E0B;font-weight:700;margin:0;">$7,500</p>
            <p style="font-family:DM Sans,sans-serif;font-size:0.7rem;color:#64748B;margin:4px 0 0 0;">avg left on the table</p>
        </div>
        <div style="width:1px;background:#1E293B;"></div>
        <div>
            <p style="font-family:DM Mono,monospace;font-size:1.4rem;color:#3B82F6;font-weight:700;margin:0;">$500K+</p>
            <p style="font-family:DM Sans,sans-serif;font-size:0.7rem;color:#64748B;margin:4px 0 0 0;">career cost of silence</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # ── Section label helper ──
    def _section(icon, title, subtitle=""):
        sub = f'<span style="font-family:DM Sans,sans-serif;font-size:0.75rem;color:#475569;margin-left:8px;">{subtitle}</span>' if subtitle else ""
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:20px 0 12px 0;">'
            f'<span style="font-size:1rem;">{icon}</span>'
            f'<span style="font-family:DM Mono,monospace;font-size:0.75rem;color:#94A3B8;letter-spacing:1.5px;font-weight:600;">{title.upper()}</span>'
            f'{sub}</div>',
            unsafe_allow_html=True,
        )

    # ═══════════════════════════════
    #  CORE — Required
    # ═══════════════════════════════
    _section("🏢", "Core Info", "Required")
    c1, c2 = st.columns(2)
    with c1:
        role = st.selectbox("Role / Title", get_available_roles(), index=1)
        years = st.slider("Years of Experience", 0, 25, 5)
        company_tier = st.selectbox("Company Tier", COMPANY_TIERS, index=5)
    with c2:
        location = st.selectbox("Location", LOCATIONS, index=5)
        offer = st.number_input("Base Salary ($)", min_value=30000, max_value=1000000, value=95000, step=5000)
        remote_policy = st.selectbox(
            "Work Arrangement",
            ["On-site", "Hybrid (2–3 days)", "Hybrid (1–2 days)", "Fully Remote", "Flexible / Your Choice"],
            index=1,
        )

    # ═══════════════════════════════
    #  COMPENSATION — Required + Optional
    # ═══════════════════════════════
    _section("💰", "Compensation", "Signing bonus & bonus target")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        signing_bonus = st.number_input("Signing Bonus ($)", min_value=0, max_value=500000, value=0, step=1000,
                                        help="One-time bonus paid on joining.")
    with cc2:
        annual_bonus_pct = st.number_input("Annual Bonus Target (%)", min_value=0, max_value=100, value=0, step=1,
                                           help="On-target bonus as % of base. Leave 0 if not applicable.")
    with cc3:
        relocation = st.number_input("Relocation Package ($)", min_value=0, max_value=100000, value=0, step=500,
                                     help="Company-paid relocation assistance.")

    # ═══════════════════════════════
    #  EQUITY & LONG-TERM
    # ═══════════════════════════════
    _section("📈", "Equity & Long-term Incentives", "Optional — RSUs, stock options, vesting")
    with st.expander("Add equity details →", expanded=False):
        eq1, eq2 = st.columns(2)
        with eq1:
            rsu_grant = st.number_input("RSU / Stock Grant Total ($)", min_value=0, max_value=10000000, value=0, step=5000,
                                        help="Total 4-year RSU grant value at current price. Leave 0 to use estimate.")
            vesting_schedule = st.selectbox("Vesting Schedule", [
                "4-year (25% / year)", "4-year (1-year cliff, monthly after)",
                "3-year (33% / year)", "3-year (1-year cliff, monthly after)",
                "2-year (50% / year)", "Immediate", "Other",
            ])
            cliff_months = st.selectbox("Cliff Period", ["None", "6 months", "1 year", "2 years"])
        with eq2:
            stock_options = st.number_input("Stock Options (# shares)", min_value=0, max_value=10000000, value=0, step=100,
                                            help="For startups offering stock options instead of / in addition to RSUs.")
            strike_price = st.number_input("Strike Price per Share ($)", min_value=0.0, max_value=10000.0, value=0.0, step=0.01,
                                           help="Exercise price for stock options (startup offers).", format="%.2f")
            annual_refresher_pct = st.number_input("Annual Refresher Grant (% of initial)", min_value=0, max_value=100, value=0, step=5,
                                                    help="Yearly refresh grant as % of initial RSU grant. Typical: 15–25%.")

    # ═══════════════════════════════
    #  BENEFITS
    # ═══════════════════════════════
    _section("🏥", "Benefits Package", "Optional — health, retirement, time off")
    with st.expander("Add benefits details →", expanded=False):
        b1, b2, b3 = st.columns(3)
        with b1:
            health_coverage = st.selectbox("Health Insurance", [
                "Not specified", "100% employer-paid (employee)", "100% employer-paid (family)",
                "80% employer-paid", "70% employer-paid", "50% employer-paid", "Employee-paid (HSA)",
            ])
            dental_vision = st.selectbox("Dental & Vision", [
                "Not specified", "Fully covered", "Partially covered (employer)", "Employee-paid",
            ])
        with b2:
            k401_match = st.selectbox("401(k) / Retirement Match", [
                "Not specified", "No match", "50% up to 3%", "50% up to 6%",
                "100% up to 3%", "100% up to 4%", "100% up to 6%", "Pension plan",
            ])
            k401_vest = st.selectbox("401(k) Vesting", [
                "Not specified", "Immediate", "1-year cliff", "2-year cliff",
                "3-year graded", "4-year graded", "6-year graded",
            ])
        with b3:
            pto_days = st.number_input("PTO / Vacation Days", min_value=0, max_value=365, value=0, step=1,
                                       help="Annual paid vacation days. Enter 0 if unlimited or not specified.")
            pto_type = st.selectbox("PTO Policy", ["Not specified", "Accrued", "Front-loaded", "Unlimited", "Flex / No formal policy"])
            parental_leave = st.number_input("Parental Leave (weeks)", min_value=0, max_value=52, value=0, step=1,
                                             help="Paid parental leave weeks offered.")

    # ═══════════════════════════════
    #  PERKS & WORK STYLE
    # ═══════════════════════════════
    _section("✨", "Perks & Other Benefits", "Optional — stipends, development, flexibility")
    with st.expander("Add perks details →", expanded=False):
        p1, p2 = st.columns(2)
        with p1:
            prof_dev_budget = st.number_input("Professional Dev Budget ($/yr)", min_value=0, max_value=50000, value=0, step=500,
                                              help="Annual budget for courses, conferences, certifications.")
            home_office_stipend = st.number_input("Home Office / Equipment Stipend ($)", min_value=0, max_value=10000, value=0, step=100,
                                                  help="One-time or annual equipment allowance.")
            wellness_stipend = st.number_input("Wellness / Gym Stipend ($/yr)", min_value=0, max_value=5000, value=0, step=100)
        with p2:
            performance_review = st.selectbox("Performance Review Cycle", [
                "Not specified", "Annual", "Semi-annual (every 6 months)",
                "Quarterly", "Continuous / Ongoing",
            ])
            start_date_flex = st.selectbox("Start Date Flexibility", [
                "Not specified", "Fixed / Immediate", "Flexible (2–4 weeks)", "Flexible (1–2 months)", "Negotiable",
            ])
            meal_stipend = st.number_input("Meal / Commuter Stipend ($/mo)", min_value=0, max_value=1000, value=0, step=25)

    st.write("")
    if st.button("🔍  ANALYZE MY OFFER", use_container_width=True):
        # Resolve bonus: if user gave explicit %, compute it; else 0
        computed_bonus_est = round(offer * annual_bonus_pct / 100) if annual_bonus_pct > 0 else 0
        st.session_state.profile = {
            # Core
            "role": role,
            "location": location,
            "years_exp": years,
            "company_tier": company_tier,
            "offer": offer,
            "remote_policy": remote_policy,
            # Compensation
            "bonus": signing_bonus,
            "annual_bonus_pct": annual_bonus_pct,
            "annual_bonus_est": computed_bonus_est,
            "relocation": relocation,
            # Equity
            "rsu_grant": rsu_grant,
            "vesting_schedule": vesting_schedule,
            "cliff_months": cliff_months,
            "stock_options": stock_options,
            "strike_price": strike_price,
            "annual_refresher_pct": annual_refresher_pct,
            # Benefits
            "health_coverage": health_coverage,
            "dental_vision": dental_vision,
            "k401_match": k401_match,
            "k401_vest": k401_vest,
            "pto_days": pto_days,
            "pto_type": pto_type,
            "parental_leave": parental_leave,
            # Perks
            "prof_dev_budget": prof_dev_budget,
            "home_office_stipend": home_office_stipend,
            "wellness_stipend": wellness_stipend,
            "performance_review": performance_review,
            "start_date_flex": start_date_flex,
            "meal_stipend": meal_stipend,
        }
        st.session_state.market = estimate_market_value(role, location, years, company_tier)
        st.session_state.analysis = analyze_offer(offer, st.session_state.market)
        st.session_state.step = "market"
        st.rerun()


# ═══════════════════════════════════════════════
#  STEP 2: MARKET ANALYSIS
# ═══════════════════════════════════════════════
elif st.session_state.step == "market":
    market = st.session_state.market
    analysis = st.session_state.analysis
    profile = st.session_state.profile

    st.markdown("### 📊 Market Analysis")

    # ─── Verdict card ───
    is_underpaid = analysis["gap_pct"] > 0
    verdict_class = "verdict-underpaid" if is_underpaid else "verdict-competitive"
    st.markdown(
        f'<div class="{verdict_class} verdict-card">'
        f'<p style="font-family:DM Mono,monospace;font-size:0.7rem;letter-spacing:1.5px;'
        f'color:{"#F87171" if is_underpaid else "#10B981"};">'
        f'{"⚠ BELOW MARKET" if is_underpaid else "✓ AT OR ABOVE MARKET"}</p>'
        f'<p style="font-size:1.8rem;font-weight:700;margin:4px 0;">'
        f'{analysis["emoji"]} {analysis["message"]}</p>'
        + (f'<p style="color:#94A3B8;">That\'s approximately '
           f'<span style="color:#F87171;font-weight:600;">${analysis["annual_loss"]:,}</span> '
           f'left on the table annually '
           f'(<span style="color:#F87171;">${analysis["five_year_loss"]:,}</span> over 5 years)</p>'
           if is_underpaid else '')
        + '</div>',
        unsafe_allow_html=True,
    )

    # ─── Salary range chart ───
    fig = go.Figure()

    # Range bar
    fig.add_trace(go.Bar(
        x=[market["p75"] - market["p25"]],
        y=["Market Range"],
        base=[market["p25"]],
        orientation="h",
        marker=dict(
            color="rgba(16,185,129,0.25)",
            line=dict(color="#10B981", width=2),
        ),
        name="Market Range (P25–P75)",
        hovertemplate=f'P25: ${market["p25"]:,}<br>P75: ${market["p75"]:,}<extra></extra>',
    ))

    # Offer marker
    fig.add_trace(go.Scatter(
        x=[profile["offer"]],
        y=["Market Range"],
        mode="markers+text",
        marker=dict(size=20, color="#EF4444", symbol="diamond"),
        text=[f'Your Offer: ${profile["offer"]:,}'],
        textposition="top center",
        textfont=dict(color="#F87171", size=12),
        name="Your Offer",
    ))

    # Median marker
    fig.add_trace(go.Scatter(
        x=[market["median"]],
        y=["Market Range"],
        mode="markers+text",
        marker=dict(size=18, color="#10B981", symbol="line-ns-open", line=dict(width=4)),
        text=[f'Median: ${market["median"]:,}'],
        textposition="bottom center",
        textfont=dict(color="#10B981", size=12),
        name="Market Median",
    ))

    fig.update_layout(
        height=200,
        margin=dict(l=30, r=30, t=30, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,1)",
        font=dict(family="DM Mono, monospace", color="#94A3B8"),
        showlegend=True,
        legend=dict(orientation="h", y=-0.4, font=dict(size=10)),
        xaxis=dict(
            gridcolor="rgba(30,41,59,0.8)",
            gridwidth=1,
            tickprefix="$",
            tickformat=",",
        ),
        yaxis=dict(visible=False),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ─── Metrics row ───
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="metric-card"><p class="metric-label">P25</p>'
            f'<p class="metric-value" style="color:#F59E0B;">${market["p25"]:,}</p></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-card"><p class="metric-label">MEDIAN</p>'
            f'<p class="metric-value" style="color:#10B981;">${market["median"]:,}</p></div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="metric-card"><p class="metric-label">P75</p>'
            f'<p class="metric-value" style="color:#3B82F6;">${market["p75"]:,}</p></div>',
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f'<div class="metric-card"><p class="metric-label">YOUR OFFER</p>'
            f'<p class="metric-value" style="color:#F87171;">${profile["offer"]:,}</p></div>',
            unsafe_allow_html=True,
        )

    # ─── Total Compensation Breakdown ───
    st.markdown('<hr style="border-color:#1E293B;margin:28px 0 20px 0;">', unsafe_allow_html=True)
    st.markdown("### 💼 Total Compensation Breakdown")
    st.markdown(
        '<p style="color:#64748B;font-size:0.85rem;margin-bottom:8px;">'
        'Estimated first-year total compensation including base, equity, bonus, and benefits.</p>',
        unsafe_allow_html=True,
    )

    # Build compensation breakdown — use entered values, fall back to tier estimates
    tier = profile["company_tier"]
    base_sal = profile["offer"]
    signing_bonus = profile.get("bonus", 0)
    relocation_val = profile.get("relocation", 0)

    _equity_pct = {
        "FAANG / Big Tech": 1.00, "Unicorn Startup": 0.80, "Mid-size Tech": 0.50,
        "Non-tech / Enterprise": 0.20, "Early-stage Startup": 0.40, "Other": 0.30,
    }
    _bonus_pct = {
        "FAANG / Big Tech": 0.15, "Unicorn Startup": 0.12, "Mid-size Tech": 0.10,
        "Non-tech / Enterprise": 0.10, "Early-stage Startup": 0.08, "Other": 0.10,
    }
    _benefits = {
        "FAANG / Big Tech": 28000, "Unicorn Startup": 22000, "Mid-size Tech": 18000,
        "Non-tech / Enterprise": 18000, "Early-stage Startup": 12000, "Other": 15000,
    }

    # Equity: use actual RSU grant if provided, otherwise estimate
    rsu_entered = profile.get("rsu_grant", 0)
    equity_grant_total = rsu_entered if rsu_entered > 0 else round(base_sal * _equity_pct.get(tier, 0.30))
    equity_year1 = round(equity_grant_total / 4)

    # Annual bonus: use entered % if provided, otherwise estimate
    if profile.get("annual_bonus_pct", 0) > 0:
        annual_bonus_est = profile.get("annual_bonus_est", 0)
        bonus_source = f"{profile['annual_bonus_pct']}% target (entered)"
    else:
        annual_bonus_est = round(base_sal * _bonus_pct.get(tier, 0.10))
        bonus_source = f"~{round(_bonus_pct.get(tier, 0.10)*100)}% estimated"

    # Refresher rate: use entered % or default to 18%
    refresher_pct = profile.get("annual_refresher_pct", 0) / 100 if profile.get("annual_refresher_pct", 0) > 0 else 0.18

    # Benefits: base estimate + entered stipends
    prof_dev = profile.get("prof_dev_budget", 0)
    home_office = profile.get("home_office_stipend", 0)
    wellness = profile.get("wellness_stipend", 0)
    meal_mo = profile.get("meal_stipend", 0)
    meal_annual = meal_mo * 12
    benefits_est = _benefits.get(tier, 15000) + prof_dev + home_office + wellness + meal_annual

    total_first_year = base_sal + equity_year1 + annual_bonus_est + signing_bonus + relocation_val + benefits_est

    col_donut, col_breakdown = st.columns([1, 1])

    with col_donut:
        d_labels = ["Base Salary", "Equity (Yr 1)", "Annual Bonus", "Sign-On Bonus", "Relocation", "Benefits & Perks"]
        d_values = [base_sal, equity_year1, annual_bonus_est, signing_bonus, relocation_val, benefits_est]
        d_colors = ["#10B981", "#3B82F6", "#F59E0B", "#EC4899", "#F97316", "#A78BFA"]
        filtered = [(l, v, c) for l, v, c in zip(d_labels, d_values, d_colors) if v > 0]
        fl, fv, fc = zip(*filtered) if filtered else ([], [], [])

        fig_donut = go.Figure(data=[go.Pie(
            labels=list(fl), values=list(fv), hole=0.62,
            marker=dict(colors=list(fc), line=dict(color="#0F172A", width=2)),
            textinfo="none",
            hovertemplate="%{label}: $%{value:,.0f} (%{percent:.1%})<extra></extra>",
        )])
        fig_donut.update_layout(
            height=300,
            margin=dict(l=0, r=110, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Mono, monospace", color="#94A3B8", size=11),
            showlegend=True,
            legend=dict(orientation="v", x=1.0, y=0.5, yanchor="middle",
                        font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            annotations=[dict(
                text=f"<b>${total_first_year:,}</b>",
                x=0.36, y=0.55, xanchor="center",
                font=dict(family="DM Mono, monospace", size=15, color="#F8FAFC"),
                showarrow=False,
            ), dict(
                text="Total Yr 1",
                x=0.36, y=0.38, xanchor="center",
                font=dict(family="DM Sans, sans-serif", size=10, color="#64748B"),
                showarrow=False,
            )],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_breakdown:
        comp_items = [
            ("Base Salary", base_sal, "#10B981"),
            (f"Equity Yr 1", equity_year1, "#3B82F6"),
            (f"Annual Bonus", annual_bonus_est, "#F59E0B"),
            ("Sign-On Bonus", signing_bonus, "#EC4899"),
            ("Relocation", relocation_val, "#F97316"),
            ("Benefits & Perks", benefits_est, "#A78BFA"),
        ]
        bar_labels = [lbl for lbl, val, clr in comp_items if val > 0]
        bar_values = [val for lbl, val, clr in comp_items if val > 0]
        bar_colors = [clr for lbl, val, clr in comp_items if val > 0]

        fig_bar = go.Figure(go.Bar(
            x=bar_values,
            y=bar_labels,
            orientation="h",
            marker=dict(color=bar_colors, line=dict(color="rgba(0,0,0,0)", width=0)),
            text=[f"${v:,}" for v in bar_values],
            textposition="outside",
            textfont=dict(family="DM Mono, monospace", size=11, color="#CBD5E1"),
            hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
        ))
        fig_bar.update_layout(
            height=300,
            margin=dict(l=10, r=80, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,1)",
            font=dict(family="DM Mono, monospace", color="#94A3B8", size=11),
            showlegend=False,
            xaxis=dict(
                tickprefix="$", tickformat=",",
                gridcolor="rgba(30,41,59,0.8)", gridwidth=1,
                zeroline=False,
            ),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", autorange="reversed"),
            bargap=0.35,
            annotations=[dict(
                text=f"Total: ${total_first_year:,}",
                xref="paper", yref="paper",
                x=0.5, y=1.08, xanchor="center",
                font=dict(family="DM Mono, monospace", size=13, color="#F8FAFC"),
                showarrow=False,
            )],
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.caption(f"ℹ Equity and benefits are estimates based on {tier} tier benchmarks.")

    # ─── Equity Projection (4-Year) ───
    st.markdown('<div style="margin-top:28px;"></div>', unsafe_allow_html=True)
    st.markdown("#### 📈 Equity Projections — 4-Year Vest + Annual Refreshers")
    st.markdown(
        '<p style="color:#64748B;font-size:0.8rem;margin-bottom:4px;">'
        'Drag the slider to model how stock price appreciation affects your equity value over the vesting period.</p>',
        unsafe_allow_html=True,
    )
    growth_rate = st.slider("Annual Growth Rate", 0, 50, 20, format="%d%%", key="equity_growth_slider")
    g = growth_rate / 100

    # Initial grant: 25% cliff/year × growth compounding
    init_per_yr = equity_grant_total / 4
    # Annual refresher grant: use entered % or default 18%
    refresh_grant = equity_grant_total * refresher_pct

    init_vals = [
        round(init_per_yr),
        round(init_per_yr * (1 + g)),
        round(init_per_yr * (1 + g) ** 2),
        round(init_per_yr * (1 + g) ** 3),
    ]
    # Refreshers accumulate: yr2 gets Refresh1 vest, yr3 gets R1+R2, yr4 gets R1+R2+R3
    refresh_vals = [
        0,
        round(refresh_grant * 0.25),
        round(refresh_grant * 0.25 * (1 + g) + refresh_grant * 0.25),
        round(refresh_grant * 0.25 * (1 + g) ** 2 + refresh_grant * 0.25 * (1 + g) + refresh_grant * 0.25),
    ]
    eq_years = ["YR 1", "YR 2", "YR 3", "YR 4"]
    eq_totals = [i + r for i, r in zip(init_vals, refresh_vals)]

    fig_eq = go.Figure()
    fig_eq.add_trace(go.Bar(
        name="Initial Grant",
        x=eq_years, y=init_vals,
        marker=dict(color="#3B82F6", opacity=0.9, line=dict(color="#2563EB", width=1)),
        hovertemplate="Initial Grant: $%{y:,.0f}<extra></extra>",
    ))
    fig_eq.add_trace(go.Bar(
        name="Refreshers",
        x=eq_years, y=refresh_vals,
        marker=dict(
            color="rgba(59,130,246,0.30)",
            pattern_shape="/", pattern_fillmode="overlay",
            line=dict(color="#3B82F6", width=1),
        ),
        hovertemplate="Refreshers: $%{y:,.0f}<extra></extra>",
    ))
    for yr, total in zip(eq_years, eq_totals):
        if total > 0:
            fig_eq.add_annotation(
                x=yr, y=total, text=f"${total:,}",
                showarrow=False, yshift=10,
                font=dict(family="DM Mono, monospace", size=10, color="#CBD5E1"),
            )
    fig_eq.update_layout(
        barmode="stack",
        height=320,
        margin=dict(l=30, r=30, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,1)",
        font=dict(family="DM Mono, monospace", color="#94A3B8"),
        legend=dict(orientation="h", y=-0.22, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickprefix="$", tickformat=",", gridcolor="rgba(30,41,59,0.8)", gridwidth=1, zeroline=False),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        bargap=0.38,
    )
    st.plotly_chart(fig_eq, use_container_width=True)

    # ── Equity summary stats ──
    cumulative_eq = sum(eq_totals)
    st.markdown(f'''
    <div style="background:rgba(59,130,246,0.07);border:1px solid rgba(59,130,246,0.18);
    border-radius:12px;padding:14px 24px;display:flex;justify-content:space-around;text-align:center;margin-bottom:8px;">
        <div>
            <p style="font-family:DM Mono,monospace;font-size:1.1rem;color:#3B82F6;font-weight:700;margin:0;">
                ${eq_totals[3]:,}</p>
            <p style="font-family:DM Sans,sans-serif;font-size:0.7rem;color:#64748B;margin:4px 0 0 0;">Year 4 equity value</p>
        </div>
        <div style="width:1px;background:#1E293B;"></div>
        <div>
            <p style="font-family:DM Mono,monospace;font-size:1.1rem;color:#10B981;font-weight:700;margin:0;">
                ${cumulative_eq:,}</p>
            <p style="font-family:DM Sans,sans-serif;font-size:0.7rem;color:#64748B;margin:4px 0 0 0;">4-year cumulative equity</p>
        </div>
        <div style="width:1px;background:#1E293B;"></div>
        <div>
            <p style="font-family:DM Mono,monospace;font-size:1.1rem;color:#F59E0B;font-weight:700;margin:0;">
                {growth_rate}%</p>
            <p style="font-family:DM Sans,sans-serif;font-size:0.7rem;color:#64748B;margin:4px 0 0 0;">annual growth applied</p>
        </div>
    </div>
    <p style="font-family:DM Sans,sans-serif;font-size:0.68rem;color:#475569;margin:0 0 20px 0;">
        ℹ Refreshers modeled at {round(refresher_pct*100)}% of initial grant/year {"(entered)" if profile.get("annual_refresher_pct",0) > 0 else "(estimated — enter your refresher rate in the profile for precision)"}. Figures are illustrative.
    </p>''', unsafe_allow_html=True)

    # ─── Benefits & Perks Summary ───
    _has_benefits = any([
        profile.get("health_coverage", "Not specified") not in ("Not specified", ""),
        profile.get("k401_match", "Not specified") not in ("Not specified", ""),
        profile.get("pto_days", 0) > 0,
        profile.get("pto_type", "Not specified") not in ("Not specified", ""),
        profile.get("parental_leave", 0) > 0,
        profile.get("dental_vision", "Not specified") not in ("Not specified", ""),
        profile.get("performance_review", "Not specified") not in ("Not specified", ""),
        profile.get("start_date_flex", "Not specified") not in ("Not specified", ""),
        profile.get("remote_policy", ""),
        profile.get("stock_options", 0) > 0,
    ])
    if _has_benefits:
        st.markdown('<hr style="border-color:#1E293B;margin:8px 0 16px 0;">', unsafe_allow_html=True)
        st.markdown("### 🏷 Full Benefits & Offer Summary")

        def _benefit_chip(icon, label, value, color="#CBD5E1"):
            if value and str(value) not in ("Not specified", "0", "0.0", ""):
                return (f'<div style="display:flex;align-items:center;gap:8px;padding:8px 14px;'
                        f'background:rgba(30,41,59,0.6);border:1px solid #1E293B;border-radius:10px;">'
                        f'<span style="font-size:1rem;">{icon}</span>'
                        f'<div><p style="font-family:DM Mono,monospace;font-size:0.65rem;color:#475569;'
                        f'letter-spacing:1px;margin:0;">{label.upper()}</p>'
                        f'<p style="font-family:DM Sans,sans-serif;font-size:0.82rem;color:{color};'
                        f'font-weight:500;margin:2px 0 0 0;">{value}</p></div></div>')
            return ""

        chips = [
            _benefit_chip("🏥", "Health Insurance", profile.get("health_coverage", ""), "#10B981"),
            _benefit_chip("🦷", "Dental & Vision", profile.get("dental_vision", ""), "#10B981"),
            _benefit_chip("🏦", "401(k) Match", profile.get("k401_match", ""), "#3B82F6"),
            _benefit_chip("⏳", "401(k) Vesting", profile.get("k401_vest", ""), "#3B82F6"),
            _benefit_chip("🌴", "PTO Policy",
                          f"{profile.get('pto_days',0)} days / yr ({profile.get('pto_type','')})"
                          if profile.get('pto_days',0) > 0 else profile.get('pto_type',''), "#F59E0B"),
            _benefit_chip("👶", "Parental Leave",
                          f"{profile.get('parental_leave',0)} weeks" if profile.get('parental_leave',0) > 0 else "", "#EC4899"),
            _benefit_chip("🏠", "Work Arrangement", profile.get("remote_policy", ""), "#A78BFA"),
            _benefit_chip("📊", "Performance Review", profile.get("performance_review", ""), "#94A3B8"),
            _benefit_chip("📅", "Start Date", profile.get("start_date_flex", ""), "#94A3B8"),
            _benefit_chip("📚", "Professional Dev",
                          f"${profile.get('prof_dev_budget',0):,}/yr" if profile.get('prof_dev_budget',0) > 0 else "", "#F97316"),
            _benefit_chip("💻", "Home Office Stipend",
                          f"${profile.get('home_office_stipend',0):,}" if profile.get('home_office_stipend',0) > 0 else "", "#F97316"),
            _benefit_chip("💪", "Wellness Stipend",
                          f"${profile.get('wellness_stipend',0):,}/yr" if profile.get('wellness_stipend',0) > 0 else "", "#F97316"),
            _benefit_chip("🍽", "Meal / Commuter",
                          f"${profile.get('meal_stipend',0):,}/mo" if profile.get('meal_stipend',0) > 0 else "", "#F97316"),
            _benefit_chip("📉", "Stock Options",
                          f"{profile.get('stock_options',0):,} options @ ${profile.get('strike_price',0):.2f}/share"
                          if profile.get('stock_options',0) > 0 else "", "#3B82F6"),
        ]
        chips = [c for c in chips if c]
        if chips:
            # 3-column grid
            cols_per_row = 3
            for row_start in range(0, len(chips), cols_per_row):
                row_chips = chips[row_start:row_start + cols_per_row]
                row_html = f'<div style="display:grid;grid-template-columns:repeat({cols_per_row},1fr);gap:10px;margin-bottom:10px;">'
                row_html += "".join(row_chips)
                row_html += "</div>"
                st.markdown(row_html, unsafe_allow_html=True)

    # ─── Adjustment breakdown ───
    with st.expander("📐 Salary Adjustment Breakdown"):
        adj = market["adjustments"]
        st.write(f"**Location multiplier** ({profile['location']}): ×{adj['location_multiplier']}")
        st.write(f"**Experience multiplier** ({profile['years_exp']} yrs): ×{adj['experience_multiplier']}")
        st.write(f"**Company tier** ({profile['company_tier']}): ×{adj['company_multiplier']}")
        st.write(f"**Combined multiplier**: ×{adj['total_multiplier']}")

    st.write("")
    col_back, col_next = st.columns([1, 3])
    with col_back:
        if st.button("← Back"):
            st.session_state.step = "profile"
            st.rerun()
    with col_next:
        if st.button("🎯  START NEGOTIATION SIM", use_container_width=True):
            engine = NegotiationEngine(st.session_state.profile, st.session_state.market)
            opening = engine.get_opening()
            st.session_state.negotiation = engine
            st.session_state.chat_history = [{"role": "hm", "text": opening}]
            st.session_state.coaching_results = []
            st.session_state.step = "negotiate"
            st.rerun()


# ═══════════════════════════════════════════════
#  STEP 3: NEGOTIATION SIMULATION
# ═══════════════════════════════════════════════
elif st.session_state.step == "negotiate":
    neg_top, neg_badge = st.columns([3, 1])
    with neg_top:
        st.markdown("### 🎭 Live Negotiation Simulation")
        st.markdown(
            '<p style="color:#64748B;font-size:0.85rem;">'
            'Practice negotiating with a simulated hiring manager. The AI coach analyzes every message.</p>',
            unsafe_allow_html=True,
        )
    with neg_badge:
        if st.session_state.negotiation:
            neg_eng = st.session_state.negotiation
            engine_label = neg_eng.engine_type
            deal_state = getattr(neg_eng, "deal_state", "exploring")
            _state_cfg = {
                "exploring":  ("🔍 EXPLORING",  "#64748B", "rgba(100,116,139,0.12)"),
                "negotiating":("⚡ NEGOTIATING","#F59E0B", "rgba(245,158,11,0.12)"),
                "converging": ("🤝 CONVERGING", "#3B82F6", "rgba(59,130,246,0.12)"),
                "closed":     ("✅ DEAL CLOSED","#10B981", "rgba(16,185,129,0.12)"),
            }
            _slabel, _scolor, _sbg = _state_cfg.get(deal_state, _state_cfg["exploring"])
            engine_badge = (
                'color:#022C22;background:#10B981;' if engine_label == "gemini"
                else 'color:#F59E0B;background:rgba(245,158,11,0.15);'
            )
            engine_text = "⚡ GEMINI LIVE" if engine_label == "gemini" else "📝 SCRIPTED"
            st.markdown(
                f'<div style="text-align:right;margin-top:10px;display:flex;flex-direction:column;gap:5px;align-items:flex-end;">'
                f'<span style="font-family:DM Mono,monospace;font-size:0.58rem;{engine_badge}'
                f'padding:3px 10px;border-radius:10px;font-weight:700;">{engine_text}</span>'
                f'<span style="font-family:DM Mono,monospace;font-size:0.58rem;color:{_scolor};'
                f'background:{_sbg};padding:3px 10px;border-radius:10px;border:1px solid {_scolor}55;">'
                f'{_slabel}</span></div>',
                unsafe_allow_html=True,
            )

    col_chat, col_coach = st.columns([3, 2])

    # ─── Chat column ───
    with col_chat:

        # ── Voice mode toggle ──
        voice_mode = False
        if voice_available():
            st.markdown(
                '<p style="font-family:DM Mono,monospace;font-size:0.65rem;color:#64748B;'
                'letter-spacing:1px;margin-bottom:4px;">VOICE MODE</p>',
                unsafe_allow_html=True,
            )
            st.toggle(
                "🎤 Mic input  +  🔊 Auto-play responses",
                value=False,
                key="voice_mode_toggle",
            )
            voice_mode = st.session_state.get("voice_mode_toggle", False)

        # ── Process queued voice input (set in the previous render by the mic widget) ──
        _pending = st.session_state.get("queued_voice_input")
        if _pending:
            st.session_state.queued_voice_input = None
            st.session_state.chat_history.append({"role": "user", "text": _pending})
            _coaching = analyze_message(
                _pending,
                st.session_state.profile,
                st.session_state.market,
            )
            st.session_state.coaching_results.append(_coaching)
            _scores = [r.get("power", r.get("power_level", 5)) for r in st.session_state.coaching_results]
            _avg_score = sum(_scores) / len(_scores) if _scores else 5.0
            _engine = st.session_state.negotiation
            _hm_response = _engine.respond(_pending, avg_score=_avg_score)
            st.session_state.chat_history.append({"role": "hm", "text": _hm_response})
            if voice_mode:
                with st.spinner("🔊 Generating voice response..."):
                    _tts, _tts_err = text_to_speech(_hm_response)
                    if _tts:
                        st.session_state.auto_play_audio = _tts
            st.rerun()
        chat_container = st.container(height=400)
        with chat_container:
            for msg in st.session_state.chat_history:
                if msg["role"] == "hm":
                    st.markdown(
                        f'<div class="chat-hm"><div class="chat-label">HIRING MANAGER</div>'
                        f'{msg["text"]}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="chat-user"><div class="chat-label">YOU</div>'
                        f'{msg["text"]}</div>',
                        unsafe_allow_html=True,
                    )

        # ── Silent auto-play TTS after HM responds (voice mode) ──
        if st.session_state.get("auto_play_audio"):
            st.markdown(autoplay_audio_html(st.session_state.auto_play_audio), unsafe_allow_html=True)
            st.session_state.auto_play_audio = None

        # ── Mic input (voice mode on) ──
        if voice_available() and voice_mode:
            st.markdown(
                '<p style="font-size:0.8rem;color:#64748B;margin:12px 0 4px;">'
                '🎤 Record your response — or type below:</p>',
                unsafe_allow_html=True,
            )
            audio_value = st.audio_input("Click to record", key="mic_input", label_visibility="collapsed")
            if audio_value is not None:
                _raw = audio_value.read()
                _hash = hash(_raw)
                if _hash != st.session_state.last_audio_hash:
                    st.session_state.last_audio_hash = _hash
                    with st.spinner("🎙️ Transcribing your response..."):
                        _transcribed, _stt_err = speech_to_text(_raw)
                    if _transcribed:
                        st.session_state.queued_voice_input = _transcribed
                        st.rerun()
                    else:
                        st.warning(_stt_err or "Couldn't transcribe — try speaking clearly, or type below.")

        # ── Manual listen button (voice mode off) ──
        elif voice_available() and not voice_mode:
            _last_hm = [m for m in st.session_state.chat_history if m["role"] == "hm"]
            if _last_hm:
                if st.button("🔊 Listen to Hiring Manager", key="voice_btn"):
                    with st.spinner("Generating voice..."):
                        _audio, _err = text_to_speech(_last_hm[-1]["text"])
                        if _audio:
                            st.markdown(autoplay_audio_html(_audio), unsafe_allow_html=True)
                        else:
                            st.warning(_err or "Voice generation failed")

        # ── Text chat input (always present) ──
        _hint = "🎤 Voice mode on — or type here too..." if voice_mode else "Type your negotiation response..."
        user_input = st.chat_input(_hint)
        st.markdown(
            '<p style="font-family:DM Mono,monospace;font-size:0.6rem;color:#334155;text-align:center;margin-top:4px;">'
            'Press Enter to send  •  Tip: anchor with specific numbers like "$135,000"</p>',
            unsafe_allow_html=True,
        )
        if user_input:
            st.session_state.chat_history.append({"role": "user", "text": user_input})
            coaching = analyze_message(
                user_input,
                st.session_state.profile,
                st.session_state.market,
            )
            st.session_state.coaching_results.append(coaching)
            _all_scores = [r.get("power", r.get("power_level", 5)) for r in st.session_state.coaching_results]
            _cur_avg = sum(_all_scores) / len(_all_scores) if _all_scores else 5.0
            engine = st.session_state.negotiation
            hm_response = engine.respond(user_input, avg_score=_cur_avg)
            st.session_state.chat_history.append({"role": "hm", "text": hm_response})
            if voice_mode:
                with st.spinner("🔊 Generating voice response..."):
                    _tts, _tts_err = text_to_speech(hm_response)
                    if _tts:
                        st.session_state.auto_play_audio = _tts
            st.rerun()

    # ─── Coach column ───
    with col_coach:
        st.markdown(
            '<p style="font-family:DM Mono,monospace;font-size:0.7rem;color:#10B981;'
            'letter-spacing:1.5px;">🧠 AI COACH</p>',
            unsafe_allow_html=True,
        )

        if st.session_state.coaching_results:
            c = st.session_state.coaching_results[-1]

            # Power meter with emoji scale
            power_color = "#10B981" if c["power"] >= 7 else "#F59E0B" if c["power"] >= 4 else "#F87171"
            power_emojis = [(range(1,3),"😰"),(range(3,5),"😐"),(range(5,7),"💪"),(range(7,9),"🔥"),(range(9,11),"👑")]
            power_emoji = next((e for r, e in power_emojis if c["power"] in r), "💪")
            st.markdown(
                f'<div class="coach-card">'
                f'<p class="metric-label">POWER LEVEL</p>'
                f'<p style="font-family:DM Mono,monospace;font-size:2rem;color:{power_color};'
                f'font-weight:700;margin:4px 0;">{power_emoji} {c["power"]}/10</p>'
                f'<div style="height:6px;background:#1E293B;border-radius:3px;margin-top:8px;">'
                f'<div style="height:100%;width:{c["power"]*10}%;background:linear-gradient(90deg,{power_color},{power_color}aa);'
                f'border-radius:3px;transition:width 0.5s ease;"></div></div></div>',
                unsafe_allow_html=True,
            )

            # Mistakes
            if c["mistakes"]:
                st.markdown(
                    '<div class="coach-card">'
                    '<p class="metric-label" style="color:#F87171;">MISTAKES</p>',
                    unsafe_allow_html=True,
                )
                for m in c["mistakes"]:
                    st.markdown(f'<p style="font-size:0.8rem;color:#94A3B8;border-left:2px solid #F87171;padding-left:10px;margin:6px 0;">{m}</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Strengths
            if c["strengths"]:
                st.markdown(
                    '<div class="coach-card">'
                    '<p class="metric-label" style="color:#10B981;">STRENGTHS</p>',
                    unsafe_allow_html=True,
                )
                for s in c["strengths"]:
                    st.markdown(f'<p style="font-size:0.8rem;color:#94A3B8;border-left:2px solid #10B981;padding-left:10px;margin:6px 0;">{s}</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Improved version
            st.markdown(
                f'<div class="coach-card">'
                f'<p class="metric-label" style="color:#3B82F6;">IMPROVED VERSION</p>'
                f'<p style="font-size:0.8rem;color:#CBD5E1;line-height:1.6;padding:8px;'
                f'background:rgba(59,130,246,0.06);border-radius:6px;border-left:2px solid #3B82F6;">'
                f'"{c["improved"]}"</p></div>',
                unsafe_allow_html=True,
            )

            # Tactical advice
            st.markdown(
                f'<div class="coach-card">'
                f'<p class="metric-label" style="color:#A78BFA;">TACTICAL ADVICE</p>'
                f'<p style="font-size:0.8rem;color:#94A3B8;line-height:1.5;">{c["advice"]}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="coach-card" style="text-align:center;padding:40px;">'
                '<p style="color:#475569;font-size:0.85rem;">Send a message to get real-time coaching feedback</p>'
                '</div>',
                unsafe_allow_html=True,
            )

    st.write("")
    col_b, col_restart, col_script = st.columns([1, 1, 2])
    with col_b:
        if st.button("← Market"):
            st.session_state.step = "market"
            st.rerun()
    with col_restart:
        if st.button("🔄 Restart"):
            engine = NegotiationEngine(st.session_state.profile, st.session_state.market)
            opening = engine.get_opening()
            st.session_state.negotiation = engine
            st.session_state.chat_history = [{"role": "hm", "text": opening}]
            st.session_state.coaching_results = []
            for _k in ["last_audio_hash", "queued_voice_input", "auto_play_audio"]:
                if _k in st.session_state:
                    del st.session_state[_k]
            st.rerun()
    with col_script:
        user_messages = [m for m in st.session_state.chat_history if m["role"] == "user"]
        if st.button("📝  GET MY SCRIPT", use_container_width=True, disabled=len(user_messages) < 1):
            transcript = st.session_state.negotiation.get_transcript()
            st.session_state.script_data = generate_script(
                st.session_state.profile,
                st.session_state.market,
                transcript,
            )
            st.session_state.step = "script"
            st.rerun()


# ═══════════════════════════════════════════════
#  STEP 4: SCRIPT OUTPUT
# ═══════════════════════════════════════════════
elif st.session_state.step == "script":
    sd = st.session_state.script_data

    st.markdown("### 📝 Your Personalized Negotiation Script")
    st.markdown(
        '<p style="color:#64748B;font-size:0.85rem;">'
        'Tailored to your profile and practice session. Use this in your real negotiation.</p>',
        unsafe_allow_html=True,
    )

    # ─── Confidence score ───
    conf_color = "#10B981" if sd["confidence"] >= 75 else "#F59E0B" if sd["confidence"] >= 50 else "#F87171"
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="metric-card"><p class="metric-label">TARGET NUMBER</p>'
            f'<p class="metric-value" style="color:#10B981;">${sd["target"]:,}</p></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card"><p class="metric-label">FALLBACK</p>'
            f'<p class="metric-value" style="color:#F59E0B;">${sd["fallback_target"]:,}</p></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-card"><p class="metric-label">CONFIDENCE</p>'
            f'<p class="metric-value" style="color:{conf_color};">{sd["confidence"]}%</p></div>',
            unsafe_allow_html=True,
        )

    st.write("")

    # ─── Opening script ───
    st.markdown("#### 🎬 Opening Script — Say This First")
    st.markdown(f'<div class="script-block">{sd["opening"]}</div>', unsafe_allow_html=True)

    if voice_available():
        if st.button("🔊 Hear Your Opening Script", key="voice_script"):
            with st.spinner("Generating voice..."):
                audio, _err = text_to_speech(sd["opening"])
                if audio:
                    st.markdown(autoplay_audio_html(audio), unsafe_allow_html=True)
                else:
                    st.warning(_err or "Voice generation failed")

    # ─── Target justification ───
    with st.expander("🎯 Target Justification"):
        st.markdown(sd["target_justification"])

    # ─── Fallback ───
    st.markdown("#### 🛡️ Fallback — If They Push Back")
    st.markdown(f'<div class="script-block">{sd["fallback"]}</div>', unsafe_allow_html=True)

    # ─── Closing ───
    st.markdown("#### 🤝 Closing Statement")
    st.markdown(f'<div class="script-block">{sd["closing"]}</div>', unsafe_allow_html=True)

    # ─── Expected outcome ───
    st.markdown("#### 📈 Expected Outcome")
    st.markdown(f'<div class="script-block">{sd["expected_outcome"]}</div>', unsafe_allow_html=True)

    # ─── Pro tips ───
    with st.expander("💡 Pro Tips"):
        for i, tip in enumerate(sd["tips"], 1):
            st.write(f"**{i}.** {tip}")

    st.write("")
    st.divider()
    st.markdown("#### 🔐 Save & Prove")
    save_col, chain_col = st.columns(2)

    with save_col:
        if db_available() and not st.session_state.session_saved:
            if st.button("💾 Save Session to MongoDB", use_container_width=True):
                session_data = {
                    "profile": st.session_state.profile,
                    "market": st.session_state.market,
                    "analysis": st.session_state.analysis,
                    "transcript": [{"role": m["role"], "text": m["text"]} for m in st.session_state.chat_history],
                    "script": {
                        "target": sd["target"],
                        "confidence": sd["confidence"],
                    },
                }
                session_id = save_session(session_data)
                if session_id:
                    st.session_state.session_saved = True
                    st.success(f"Session saved! ID: {session_id[:12]}...")
                else:
                    st.error("Failed to save session")
        elif st.session_state.session_saved:
            st.success("✅ Session saved to MongoDB")
        elif not db_available():
            st.info("MongoDB not connected — add connection string to config.py")

    with chain_col:
        if solana_available():
            if st.button("⛓️ Create Salary Proof (Solana)", use_container_width=True):
                outcome = {
                    "role": st.session_state.profile.get("role"),
                    "location": st.session_state.profile.get("location"),
                    "years_exp": st.session_state.profile.get("years_exp"),
                    "offer": st.session_state.profile.get("offer"),
                    "median": st.session_state.market.get("median"),
                    "gap_pct": st.session_state.analysis.get("gap_pct"),
                }
                proof = create_salary_proof(outcome)
                st.session_state.blockchain_proof = proof
                if proof.get("success"):
                    if db_available():
                        save_outcome({"proof": proof, "profile_role": outcome["role"]})

            if st.session_state.blockchain_proof and st.session_state.blockchain_proof.get("success"):
                proof = st.session_state.blockchain_proof
                st.success("⛓️ Proof created!")
                st.code(
                    f"Hash: {proof['proof_hash'][:32]}...\n"
                    f"Wallet: {proof['wallet_address'][:20]}...\n"
                    f"Network: {proof['network']}",
                    language="text",
                )
                st.markdown(f"[View on Solana Explorer]({proof['explorer_url']})")
        else:
            st.info("Solana not connected — install solders and solana packages")

    st.write("")
    col_b1, col_b2 = st.columns([1, 3])
    with col_b1:
        if st.button("← Back to Practice"):
            st.session_state.step = "negotiate"
            st.rerun()
    with col_b2:
        if st.button("🔄  Start Over", use_container_width=True):
            for key in ["step", "profile", "market", "analysis", "negotiation",
                        "chat_history", "coaching_results", "script_data",
                        "audio_bytes", "session_saved", "blockchain_proof",
                        "last_audio_hash", "queued_voice_input", "auto_play_audio",
                        "voice_mode_toggle"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


# ─── Sidebar ───
with st.sidebar:
    st.markdown(
        '<p style="font-family:DM Mono,monospace;font-size:0.8rem;color:#10B981;'
        'letter-spacing:1.5px;">SYSTEM STATUS</p>',
        unsafe_allow_html=True,
    )

    voice_status = "🟢" if voice_available() else "⚪"
    voice_label = "Active" if voice_available() else "Not connected"
    voice_color = "#10B981" if voice_available() else "#475569"
    db_status = "🟢" if db_available() else "⚪"
    db_label = "Active" if db_available() else "Not connected"
    db_color = "#10B981" if db_available() else "#475569"
    sol_status = "🟢" if solana_available() else "⚪"
    sol_label = "Active" if solana_available() else "Not connected"
    sol_color = "#10B981" if solana_available() else "#475569"

    st.markdown(
        '<div style="background:#0F172A;border:1px solid #1E293B;border-radius:8px;padding:12px;margin:8px 0;">'
        '<p style="font-size:0.75rem;color:#94A3B8;margin:4px 0;">🟢 Salary Engine: <b style="color:#10B981;">Active</b></p>'
        '<p style="font-size:0.75rem;color:#94A3B8;margin:4px 0;">🟢 LLM Engine: <b style="color:#10B981;">Gemini 2.0 Flash</b></p>'
        f'<p style="font-size:0.75rem;color:#94A3B8;margin:4px 0;">{voice_status} Voice (ElevenLabs): <b style="color:{voice_color};">{voice_label}</b></p>'
        f'<p style="font-size:0.75rem;color:#94A3B8;margin:4px 0;">{sol_status} Blockchain (Solana): <b style="color:{sol_color};">{sol_label}</b></p>'
        f'<p style="font-size:0.75rem;color:#94A3B8;margin:4px 0;">{db_status} Database (MongoDB): <b style="color:{db_color};">{db_label}</b></p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    with st.expander("💡 Quick Negotiation Tips"):
        st.markdown('''
        <div style="font-size:0.75rem;color:#94A3B8;line-height:1.8;">
        <p><b style="color:#10B981;">1.</b> Always counter — never accept the first offer</p>
        <p><b style="color:#10B981;">2.</b> Use specific numbers ($127,500 not "around $130k")</p>
        <p><b style="color:#10B981;">3.</b> After your ask, stop talking — silence is power</p>
        <p><b style="color:#10B981;">4.</b> Frame as mutual value, not demands</p>
        <p><b style="color:#10B981;">5.</b> Negotiate total comp: base + bonus + equity + PTO</p>
        </div>
        ''', unsafe_allow_html=True)

    if db_available():
        st.divider()
        st.markdown(
            '<p style="font-family:DM Mono,monospace;font-size:0.7rem;color:#64748B;'
            'letter-spacing:1px;">PAST SESSIONS</p>',
            unsafe_allow_html=True,
        )
        recent = get_recent_sessions(5)
        if recent:
            for s in recent:
                role = s.get("profile", {}).get("role", "Unknown")
                offer = s.get("profile", {}).get("offer", 0)
                st.markdown(
                    f'<p style="font-size:0.7rem;color:#94A3B8;margin:2px 0;">'
                    f'{role} — ${offer:,}</p>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<p style="font-size:0.7rem;color:#475569;">No sessions yet</p>', unsafe_allow_html=True)

    st.divider()
    st.markdown(
        '<p style="font-family:DM Mono,monospace;font-size:0.6rem;color:#475569;'
        'letter-spacing:1px;text-align:center;">NEGOTIATEAI © 2026<br>HACKATHON DEMO</p>',
        unsafe_allow_html=True,
    )
