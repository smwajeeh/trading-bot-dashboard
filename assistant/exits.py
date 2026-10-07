"""Close open trades automatically from TradingView price / exit alerts.

Two kinds of webhook events are understood (alongside entry signals):

  price feed  {"event": "price", "high": 20110, "low": 20040, "price": 20090}
              Sent every bar close. If the bar's range reaches the open trade's
              TP or SL, the trade is closed as a win or loss at that level.
              If one bar touches both, we can't know which came first, so it is
              counted as a loss (the conservative choice).

  exit        {"event": "exit", "result": "tp" | "sl" | "win" | "loss", "price": 20100}
              Closes the open trade directly, e.g. from a strategy's exit alert.
"""
from datetime import timedelta

from . import trades

EXIT_RESULTS = {"tp": "win", "win": "win", "sl": "loss", "loss": "loss"}


class ExitError(ValueError):
    pass


def _num(payload, key):
    value = payload.get(key)
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ExitError(f"invalid {key}: {value!r}")


def bar_outcome(trade, high, low):
    """Return (result, exit_price, closed_by) if the bar hit TP or SL, else None."""
    tp, sl = trade["take_profit"], trade["stop_loss"]
    if tp is None or sl is None:
        return None
    if trade["direction"] == "LONG":
        hit_tp, hit_sl = high >= tp, low <= sl
    else:
        hit_tp, hit_sl = low <= tp, high >= sl
    if hit_sl:
        return "loss", sl, "auto-sl"
    if hit_tp:
        return "win", tp, "auto-tp"
    return None


def handle_event(payload, grace_seconds):
    """Process a price or exit event. Returns (closed_trade_or_None, note)."""
    event = str(payload.get("event", "")).lower()
    price = _num(payload, "price")
    if price is None:
        price = _num(payload, "close")
    high = _num(payload, "high")
    low = _num(payload, "low")
    if high is None:
        high = price
    if low is None:
        low = price

    if event in ("price", "bar"):
        if high is None or low is None:
            raise ExitError("price event needs 'high'/'low' or 'price'")
        trades.set_meta("last_bar", {"at": trades.now_utc().isoformat(),
                                     "high": high, "low": low, "price": price})

    trade = trades.current_open_trade()
    if trade is None:
        return None, "no open trade"

    if event in ("price", "bar"):
        # The bar that produced the entry signal can contain prices from before
        # the entry, so ignore bars that arrive right after the trade opened.
        opened = trades.parse_ts(trade["opened_at"])
        if trades.now_utc() - opened < timedelta(seconds=grace_seconds):
            return None, "bar ignored: trade just opened"
        outcome = bar_outcome(trade, high, low)
        if outcome is None:
            return None, "TP/SL not reached" if trade["entry"] is not None else "trade has no entry price"
        result, exit_price, closed_by = outcome
    elif event == "exit":
        result = EXIT_RESULTS.get(str(payload.get("result", "")).lower())
        if result is None:
            raise ExitError("exit event needs 'result': tp, sl, win or loss")
        exit_price = price if price is not None else (
            trade["take_profit"] if result == "win" else trade["stop_loss"])
        closed_by = "alert"
    else:
        raise ExitError(f"unknown event {event!r}")

    trades.set_result(trade["id"], result, exit_price=exit_price, closed_by=closed_by)
    return trades.get_trade(trade["id"]), f"closed as {result} ({closed_by})"
