import os
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_env_file(path=os.path.join(PROJECT_ROOT, ".env")):
    """Read KEY=VALUE lines from .env. Real environment variables win."""
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass


def _flag(name):
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


_load_env_file()


def utc_now():
    return datetime.now(timezone.utc)


class Config:
    # Shared secret that TradingView must send in the alert body.
    # If empty, the webhook accepts any request (only use that locally).
    WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

    # Password for the dashboard (HTTP basic auth, any username).
    # If empty, the dashboard is open to anyone with the URL.
    DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "")

    # Practice mode: ignores the trading window, keeps its own separate data,
    # and adds buttons to the dashboard that simulate TradingView alerts.
    PRACTICE_MODE = _flag("PRACTICE_MODE")

    # Where persistent data (the SQLite database) lives.
    DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(
        PROJECT_ROOT, "data-practice" if PRACTICE_MODE else "data")

    MARKET_TIMEZONE = os.environ.get("MARKET_TIMEZONE", "America/New_York")
    TP_POINTS = float(os.environ.get("TP_POINTS", 100))
    SL_POINTS = float(os.environ.get("SL_POINTS", 50))

    # Trading window: market open + SKIP_MINUTES until market open + WINDOW_MINUTES.
    MARKET_OPEN = os.environ.get("MARKET_OPEN", "09:30")
    SKIP_MINUTES = int(os.environ.get("SKIP_MINUTES", 15))
    WINDOW_MINUTES = int(os.environ.get("WINDOW_MINUTES", 120))

    # Daily stop rules.
    MAX_WINS = int(os.environ.get("MAX_WINS", 1))
    MAX_LOSSES = int(os.environ.get("MAX_LOSSES", 2))

    # Price-feed bars arriving this soon after a trade opens are ignored, because
    # the signal bar itself can contain prices from before the entry.
    BAR_GRACE_SECONDS = int(os.environ.get("BAR_GRACE_SECONDS", 0 if PRACTICE_MODE else 30))

    # Returns the current time as an aware UTC datetime; overridden in tests.
    CLOCK = staticmethod(utc_now)
