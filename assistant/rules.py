"""Daily discipline rules for the MSB scalping strategy.

A signal is only taken when all of these hold:
  * it is a weekday,
  * it is inside the trading window: market open + SKIP_MINUTES (the
    15-minute manipulation candle) until market open + WINDOW_MINUTES,
  * the daily stop has not been hit (MAX_WINS wins or MAX_LOSSES losses),
  * no other trade is still open.
"""
from datetime import datetime, time, timedelta

from flask import current_app

from . import trades


def window(day_dt):
    """Return (start, end) of the trading window for the given local datetime's date."""
    cfg = current_app.config
    hh, mm = (int(x) for x in cfg["MARKET_OPEN"].split(":"))
    market_open = datetime.combine(day_dt.date(), time(hh, mm), tzinfo=day_dt.tzinfo)
    return (market_open + timedelta(minutes=cfg["SKIP_MINUTES"]),
            market_open + timedelta(minutes=cfg["WINDOW_MINUTES"]))


def day_status(now=None):
    cfg = current_app.config
    now = now or trades.now_utc()
    local = now.astimezone(trades.market_tz())
    day_trades = trades.trades_for_day(local.date().isoformat())
    wins = sum(t["result"] == "win" for t in day_trades)
    losses = sum(t["result"] == "loss" for t in day_trades)
    open_trades = [t for t in day_trades if t["result"] is None]
    start, end = window(local)

    if wins >= cfg["MAX_WINS"]:
        stop_reason = f"Daily target hit ({wins} win{'s' if wins > 1 else ''}). Done for today."
    elif losses >= cfg["MAX_LOSSES"]:
        stop_reason = f"Max daily losses hit ({losses}). Stop trading for today."
    else:
        stop_reason = None

    if local.weekday() >= 5:
        window_state, window_reason = "closed", "Weekend: market closed."
    elif local < start:
        window_state = "before"
        window_reason = f"Before trading window (opens {start:%H:%M} {local.tzname()})."
    elif local >= end:
        window_state = "after"
        window_reason = f"Trading window closed at {end:%H:%M} {local.tzname()}."
    else:
        window_state, window_reason = "open", None

    return {
        "trading_day": local.date().isoformat(),
        "local_time": local.isoformat(),
        "window": {"start": start.isoformat(), "end": end.isoformat(),
                   "state": window_state, "reason": window_reason},
        "wins": wins,
        "losses": losses,
        "max_wins": cfg["MAX_WINS"],
        "max_losses": cfg["MAX_LOSSES"],
        "open_trade": open_trades[0] if open_trades else None,
        "stopped": stop_reason is not None,
        "stop_reason": stop_reason,
    }


def check_signal(status):
    """Return None if a new trade may be opened, otherwise the reason it may not."""
    if status["stopped"]:
        return status["stop_reason"]
    if status["window"]["state"] != "open" and not current_app.config["PRACTICE_MODE"]:
        return status["window"]["reason"]
    if status["open_trade"]:
        return f"Trade #{status['open_trade']['id']} is still open. Mark its result first."
    return None
