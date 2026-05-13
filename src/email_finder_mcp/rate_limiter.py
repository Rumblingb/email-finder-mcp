"""Rate limiting and pro key management for Email Finder MCP."""

import os
import json
import hashlib
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FREE_LIMIT = 50

# Demo/valid PRO keys for testing
PRO_KEYS = os.getenv("PRO_KEYS", "demo-pro-key-001,demo-pro-key-002,demo-pro-key-003").split(",")

# Stripe payment link for upgrades
STRIPE_LINK = os.getenv(
    "STRIPE_LINK",
    "https://buy.stripe.com/fZu14p8XtgAk6DKa791oI0D"
)

DATA_DIR = Path(os.getenv("DATA_DIR", str(Path.home() / ".email-finder-mcp")))
DATA_FILE = DATA_DIR / "usage.json"


def _ensure_data_dir():
    """Ensure the data directory and file exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("{}")


def _get_client_id(client_info: str) -> str:
    """Generate a consistent client ID from client info."""
    return hashlib.sha256(client_info.encode()).hexdigest()[:16]


def _load_usage():
    """Load usage data from disk."""
    _ensure_data_dir()
    try:
        return json.loads(DATA_FILE.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_usage(usage: dict):
    """Save usage data to disk."""
    _ensure_data_dir()
    DATA_FILE.write_text(json.dumps(usage, indent=2))


def is_pro_key(api_key: str) -> bool:
    """Check if an API key is a valid PRO key."""
    return api_key.strip() in PRO_KEYS


def get_usage_count(client_id: str) -> int:
    """Get the current usage count for a client."""
    usage = _load_usage()
    return usage.get(client_id, {}).get("count", 0)


def increment_usage(client_id: str) -> int:
    """Increment usage count for a client. Returns new count."""
    usage = _load_usage()
    client_data = usage.get(client_id, {"count": 0, "first_seen": int(time.time())})
    client_data["count"] += 1
    client_data["last_seen"] = int(time.time())
    usage[client_id] = client_data
    _save_usage(usage)
    return client_data["count"]


def check_rate_limit(client_info: str, api_key: str | None = None) -> dict:
    """Check if the client can make an API call.

    Returns:
        dict with:
            - allowed (bool): whether the call is allowed
            - remaining (int): remaining free calls (None for PRO)
            - is_pro (bool): whether the client is PRO
            - message (str): human-readable status
    """
    if api_key and is_pro_key(api_key):
        return {
            "allowed": True,
            "remaining": None,
            "is_pro": True,
            "message": "PRO access granted",
        }

    client_id = _get_client_id(client_info)
    current = get_usage_count(client_id)

    if current >= FREE_LIMIT:
        return {
            "allowed": False,
            "remaining": 0,
            "is_pro": False,
            "message": f"Free limit of {FREE_LIMIT} reached. Upgrade at {STRIPE_LINK}",
        }

    remaining = FREE_LIMIT - current
    return {
        "allowed": True,
        "remaining": remaining,
        "is_pro": False,
        "message": f"{remaining} free calls remaining",
    }
