"""Practice-mode endpoints: simulate TradingView alerts from the dashboard.

Only registered when PRACTICE_MODE is on. Each button builds the same payload
TradingView would send and runs it through the normal webhook handling.
"""
from flask import jsonify, request

from . import trades
from .db import get_db

DEFAULT_PRICE = 20000.0


def _last_price():
    bar = trades.get_meta("last_bar")
    return bar["price"] if bar and bar.get("price") is not None else DEFAULT_PRICE


def register(app, handle_alert):
    @app.post("/api/practice/signal")
    def practice_signal():
        direction = (request.get_json(silent=True) or {}).get("direction", "LONG")
        return handle_alert({"action": direction, "price": _last_price(), "ticker": "PRACTICE"})

    @app.post("/api/practice/bar")
    def practice_bar():
        kind = (request.get_json(silent=True) or {}).get("kind", "drift")
        trade = trades.current_open_trade()
        if trade is None or trade["entry"] is None:
            price = _last_price() + 5
            return handle_alert({"event": "price", "high": price + 3, "low": price - 3, "price": price})
        long = trade["direction"] == "LONG"
        if kind == "tp":
            price = trade["take_profit"]
        elif kind == "sl":
            price = trade["stop_loss"]
        else:
            price = trade["entry"] + (20 if long else -20)
        return handle_alert({"event": "price", "high": price + 2, "low": price - 2, "price": price})

    @app.post("/api/practice/reset")
    def practice_reset():
        db = get_db()
        db.executescript("DELETE FROM signals; DELETE FROM trades; DELETE FROM meta;")
        db.commit()
        return jsonify(status="ok")
