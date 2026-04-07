"""
salary_engine.py — Market Value Estimation Engine
Hybrid approach: static mock data + location/experience adjustments
"""

import json
import os

# ─── Location cost-of-living multipliers ───
LOCATION_MULTIPLIERS = {
    "San Francisco": 1.35,
    "New York": 1.30,
    "Seattle": 1.25,
    "Boston": 1.20,
    "Los Angeles": 1.18,
    "Austin": 1.10,
    "Denver": 1.08,
    "Portland": 1.08,
    "Chicago": 1.05,
    "Dallas": 1.03,
    "Miami": 1.02,
    "Atlanta": 1.00,
    "Remote": 1.05,
    "Other": 1.00,
}

# ─── Tech company premium tiers ───
COMPANY_PREMIUMS = {
    "FAANG / Big Tech": 1.30,
    "Unicorn Startup": 1.15,
    "Mid-size Tech": 1.05,
    "Non-tech / Enterprise": 0.95,
    "Early-stage Startup": 0.90,
    "Other": 1.00,
}

LOCATIONS = list(LOCATION_MULTIPLIERS.keys())
COMPANY_TIERS = list(COMPANY_PREMIUMS.keys())


def load_salary_data():
    """Load salary mock data from JSON file."""
    data_path = os.path.join(os.path.dirname(__file__), "data", "salary_mock.json")
    with open(data_path, "r") as f:
        return json.load(f)


def get_available_roles():
    """Return list of available roles (title-cased)."""
    data = load_salary_data()
    return [role.title() for role in data.keys()]


def estimate_market_value(role: str, location: str, years_exp: int, company_tier: str = "Other"):
    """
    Estimate market salary range for a given profile.

    Returns dict with p25, median, p75, and adjustment metadata.
    """
    data = load_salary_data()
    role_key = role.lower().strip()

    # Fallback to closest match
    if role_key not in data:
        role_key = "software engineer"

    base = data[role_key]
    loc_mult = LOCATION_MULTIPLIERS.get(location, 1.0)
    exp_mult = 1 + min(years_exp, 25) * 0.025  # 2.5% per year, cap at 25 yrs
    company_mult = COMPANY_PREMIUMS.get(company_tier, 1.0)

    total_mult = loc_mult * exp_mult * company_mult

    result = {
        "role": role,
        "location": location,
        "years_exp": years_exp,
        "company_tier": company_tier,
        "p25": round(base["p25"] * total_mult),
        "median": round(base["median"] * total_mult),
        "p75": round(base["p75"] * total_mult),
        "adjustments": {
            "location_multiplier": loc_mult,
            "experience_multiplier": round(exp_mult, 3),
            "company_multiplier": company_mult,
            "total_multiplier": round(total_mult, 3),
        },
    }

    return result


def analyze_offer(offer: int, market: dict):
    """
    Compare an offer against market data.

    Returns analysis dict with gap info and verdict.
    """
    median = market["median"]
    gap = median - offer
    gap_pct = round((gap / median) * 100) if median > 0 else 0

    if gap_pct > 20:
        verdict = "significantly_underpaid"
        emoji = "🔴"
        message = f"You are significantly underpaid — ~{gap_pct}% below market median."
    elif gap_pct > 10:
        verdict = "underpaid"
        emoji = "🟠"
        message = f"You are underpaid by ~{gap_pct}% relative to market."
    elif gap_pct > 0:
        verdict = "slightly_below"
        emoji = "🟡"
        message = f"Your offer is slightly below market (~{gap_pct}% gap)."
    elif gap_pct > -10:
        verdict = "competitive"
        emoji = "🟢"
        message = "Your offer is competitive with the market."
    else:
        verdict = "above_market"
        emoji = "🔵"
        message = "Your offer is above market — nice position!"

    return {
        "offer": offer,
        "median": median,
        "gap": gap,
        "gap_pct": gap_pct,
        "verdict": verdict,
        "emoji": emoji,
        "message": message,
        "annual_loss": max(gap, 0),
        "five_year_loss": max(gap * 5, 0),
    }
