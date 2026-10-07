"""Storage and bookkeeping for signals and trades."""
from zoneinfo import ZoneInfo

from flask import current_app

from .db import get_db

RESULTS = ("win", "loss", "void")


def now_utc():
    return current_app.config["CLOCK"]()


def market_tz():
    return ZoneInfo(current_app.config["MARKET_TIMEZONE"])


def trading_day(ts=None):
    ts = ts or now_utc()
    return ts.astimezone(market_tz()).date().isoformat()


def levels(direction, entry):
    if entry is None:
        return None, None
    tp = current_app.config["TP_POINTS"]
    sl = current_app.config["SL_POINTS"]
    if direction == "LONG":
        return entry + tp, entry - sl
    return entry - tp, entry + sl


def record_signal(signal, status, reason=None, trade_id=None):
    ts = now_utc()
    db = get_db()
    cur = db.execute(
        "INSERT INTO signals (received_at, trading_day, direction, price, ticker, raw, status, reason, trade_id)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (ts.isoformat(), trading_day(ts), signal.direction, signal.price, signal.ticker,
         signal.raw, status, reason, trade_id),
    )
    db.commit()
    return cur.lastrowid


def open_trade(signal):
    ts = now_utc()
    tp, sl = levels(signal.direction, signal.price)
    db = get_db()
    cur = db.execute(
        "INSERT INTO trades (opened_at, trading_day, direction, ticker, entry, take_profit, stop_loss)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (ts.isoformat(), trading_day(ts), signal.direction, signal.ticker, signal.price, tp, sl),
    )
    db.commit()
    return cur.lastrowid


def set_result(trade_id, result):
    if result not in RESULTS:
        raise ValueError(f"result must be one of {RESULTS}")
    db = get_db()
    cur = db.execute(
        "UPDATE trades SET result = ?, closed_at = ? WHERE id = ?",
        (result, now_utc().isoformat(), trade_id),
    )
    db.commit()
    return cur.rowcount == 1


def set_entry(trade_id, entry):
    """Set or correct the fill price of an open trade and recompute TP/SL."""
    trade = get_trade(trade_id)
    if trade is None:
        return False
    if trade["result"] is not None:
        raise ValueError("trade is already closed")
    tp, sl = levels(trade["direction"], entry)
    db = get_db()
    db.execute("UPDATE trades SET entry = ?, take_profit = ?, stop_loss = ? WHERE id = ?",
               (entry, tp, sl, trade_id))
    db.commit()
    return True


def get_trade(trade_id):
    row = get_db().execute("SELECT * FROM trades WHERE id = ?", (trade_id,)).fetchone()
    return dict(row) if row else None


def trades_for_day(day):
    rows = get_db().execute(
        "SELECT * FROM trades WHERE trading_day = ? ORDER BY id DESC", (day,)).fetchall()
    return [dict(r) for r in rows]


def recent_signals(limit=20):
    rows = get_db().execute(
        "SELECT * FROM signals ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]

