"""
blockchain.py — Solana Blockchain Integration
Stores anonymized negotiation outcomes as on-chain "proof of salary data."
Uses Solana devnet (free, no real money).
"""

import json
import hashlib
import time

try:
    from solders.keypair import Keypair
    from config import SOLANA_RPC_URL

    # Generate a demo keypair (not real money — devnet only)
    demo_keypair = Keypair()
    SOLANA_AVAILABLE = True
except ImportError:
    demo_keypair = None
    SOLANA_AVAILABLE = False
except Exception:
    demo_keypair = None
    SOLANA_AVAILABLE = False


def create_salary_proof(outcome_data: dict) -> dict:
    """
    Create a proof-of-salary-data hash that could be stored on-chain.
    For the hackathon demo, we generate the hash and proof structure.

    In production, this would be a Solana memo transaction.
    For the demo, we simulate the on-chain storage to avoid needing devnet SOL.
    """
    try:
        # Create anonymized data hash
        proof_data = {
            "role": outcome_data.get("role", "unknown"),
            "location": outcome_data.get("location", "unknown"),
            "experience_band": _experience_band(outcome_data.get("years_exp", 0)),
            "salary_band": _salary_band(outcome_data.get("offer", 0)),
            "market_band": _salary_band(outcome_data.get("median", 0)),
            "gap_pct": outcome_data.get("gap_pct", 0),
            "timestamp": int(time.time()),
        }

        # Hash the data
        data_json = json.dumps(proof_data, sort_keys=True)
        data_hash = hashlib.sha256(data_json.encode()).hexdigest()

        # Generate proof structure
        wallet_address = str(demo_keypair.pubkey()) if demo_keypair else "demo_wallet_not_available"

        return {
            "success": True,
            "proof_hash": data_hash,
            "proof_data": proof_data,
            "wallet_address": wallet_address,
            "network": "solana-devnet",
            "explorer_url": f"https://explorer.solana.com/address/{wallet_address}?cluster=devnet",
            "note": "Demo mode — hash generated locally. Production would write a Solana memo transaction.",
        }

    except Exception as e:
        print(f"Solana proof error: {e}")
        return {"success": False, "error": str(e)}


def _experience_band(years: int) -> str:
    """Anonymize experience into bands."""
    if years < 2: return "junior (0-2)"
    if years < 5: return "mid (2-5)"
    if years < 10: return "senior (5-10)"
    return "staff+ (10+)"


def _salary_band(salary: int) -> str:
    """Anonymize salary into bands."""
    band = (salary // 25000) * 25000
    return f"${band:,}-${band+25000:,}"


def get_network_status() -> dict:
    """Check Solana devnet status."""
    if not SOLANA_AVAILABLE:
        return {"connected": False, "reason": "Solana libraries not installed"}
    return {"connected": True, "network": "devnet", "rpc": SOLANA_RPC_URL}


def is_available() -> bool:
    """Check if Solana integration is available."""
    return SOLANA_AVAILABLE
