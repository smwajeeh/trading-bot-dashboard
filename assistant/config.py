import os
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)


class Config:
    # Shared secret that TradingView must send in the alert body.
    # If empty, the webhook accepts any request (only use that locally).
    WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

    # Where persistent data (the SQLite database) lives.
    DATA_DIR = os.environ.get("DATA_DIR", "data")

    MARKET_TIMEZONE = os.environ.get("MARKET_TIMEZONE", "America/New_York")
    TP_POINTS = float(os.environ.get("TP_POINTS", 100))
    SL_POINTS = float(os.environ.get("SL_POINTS", 50))

    # Returns the current time as an aware UTC datetime; overridden in tests.
    CLOCK = staticmethod(utc_now)
