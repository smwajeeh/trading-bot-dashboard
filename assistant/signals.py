"""Parse TradingView alert payloads into a normalised Signal."""
from dataclasses import dataclass
from typing import Optional

LONG_WORDS = {"long", "buy", "bull", "bullish"}
SHORT_WORDS = {"short", "sell", "bear", "bearish"}


class SignalError(ValueError):
    pass


@dataclass
class Signal:
    direction: str  # "LONG" or "SHORT"
    price: Optional[float]
    ticker: Optional[str]
    raw: str


def _direction_from_text(text):
    words = {w.strip(".,:;!()[]{}\"'").lower() for w in str(text).split()}
    is_long = bool(words & LONG_WORDS)
    is_short = bool(words & SHORT_WORDS)
    if is_long == is_short:
        return None
    return "LONG" if is_long else "SHORT"


def _to_price(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise SignalError(f"invalid price: {value!r}")


def parse_signal(payload):
    """Accepts either a JSON object or plain alert text.

    Recommended TradingView alert message:
        {"secret": "...", "action": "LONG", "price": {{close}}, "ticker": "{{ticker}}"}
    Also accepted: {"message": "MSB LONG"} or a plain-text body like "MSB SHORT".
    """
    if isinstance(payload, dict):
        text = None
        for key in ("action", "side", "direction", "message"):
            if payload.get(key):
                text = payload[key]
                break
        if text is None:
            raise SignalError("missing 'action' (LONG/SHORT)")
        price = _to_price(payload.get("price", payload.get("close")))
        ticker = payload.get("ticker") or None
        raw = str(text)
    elif isinstance(payload, str) and payload.strip():
        text, price, ticker, raw = payload, None, None, payload.strip()
    else:
        raise SignalError("empty payload")

    direction = _direction_from_text(text)
    if direction is None:
        raise SignalError(f"could not determine LONG/SHORT from {raw!r}")
    return Signal(direction=direction, price=price, ticker=ticker, raw=raw)
