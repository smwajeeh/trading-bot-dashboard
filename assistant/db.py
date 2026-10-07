import os
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at TEXT NOT NULL,          -- UTC ISO-8601
    trading_day TEXT NOT NULL,          -- YYYY-MM-DD in market timezone
    direction   TEXT NOT NULL,          -- LONG / SHORT
    price       REAL,
    ticker      TEXT,
    raw         TEXT,
    status      TEXT NOT NULL,          -- accepted / rejected
    reason      TEXT,                   -- why it was rejected
    trade_id    INTEGER REFERENCES trades(id)
);
CREATE TABLE IF NOT EXISTS trades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    opened_at   TEXT NOT NULL,
    trading_day TEXT NOT NULL,
    direction   TEXT NOT NULL,
    ticker      TEXT,
    entry       REAL,
    take_profit REAL,
    stop_loss   REAL,
    result      TEXT,                   -- NULL (open) / win / loss / void
    closed_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_trades_day ON trades(trading_day);
CREATE INDEX IF NOT EXISTS idx_signals_day ON signals(trading_day);
"""


def db_path(app):
    return os.path.join(app.config["DATA_DIR"], "assistant.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(db_path(current_app))
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    with sqlite3.connect(db_path(app)) as conn:
        conn.executescript(SCHEMA)
    app.teardown_appcontext(close_db)
