import os


class Config:
    # Shared secret that TradingView must send in the alert body.
    # If empty, the webhook accepts any request (only use that locally).
    WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

    # Where persistent data (the SQLite database) lives.
    DATA_DIR = os.environ.get("DATA_DIR", "data")
