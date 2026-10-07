import hmac
import json
import logging
import os

from flask import Flask, jsonify, request

from .config import Config
from .signals import SignalError, parse_signal

log = logging.getLogger(__name__)


def _read_payload():
    # TradingView sends text/plain unless the alert message is valid JSON,
    # so parse the body ourselves instead of relying on the Content-Type.
    data = request.get_json(force=True, silent=True)
    if data is None:
        data = request.get_data(as_text=True)
    return data


def _secret_ok(app, payload):
    expected = app.config["WEBHOOK_SECRET"]
    if not expected:
        return True
    given = payload.get("secret", "") if isinstance(payload, dict) else ""
    given = given or request.args.get("secret", "")
    return hmac.compare_digest(str(given), expected)


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)
    if not app.config["WEBHOOK_SECRET"]:
        log.warning("WEBHOOK_SECRET is not set: webhook accepts unauthenticated requests")

    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    latest_file = os.path.join(app.config["DATA_DIR"], "latest_signal.json")

    @app.post("/webhook")
    def webhook():
        payload = _read_payload()
        if not _secret_ok(app, payload):
            return jsonify(status="error", error="invalid secret"), 401
        try:
            signal = parse_signal(payload)
        except SignalError as e:
            return jsonify(status="error", error=str(e)), 400

        with open(latest_file, "w") as f:
            json.dump(signal.__dict__, f)
        log.info("Received %s signal: %s", signal.direction, signal.raw)
        return jsonify(status="ok", signal=signal.__dict__)

    @app.get("/")
    def home():
        return "Webhook is running!"

    return app
