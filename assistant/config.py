import os
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)


class Config:
    # Shared secret that TradingView must send in the alert body.
    # If empty, the webhook accepts any request (only use that locally).
    WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

    # Password for the dashboard (HTTP basic auth, any username).
    # If empty, the dashboard is open to anyone with the URL.
    DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "")

    # Where persistent data (the SQLite database) lives.
    DATA_DIR = os.environ.get("DATA_DIR", "data")

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

    # Returns the current time as an aware UTC datetime; overridden in tests.
    CLOCK = staticmethod(utc_now)
