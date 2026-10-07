import hmac
import logging

from flask import Flask, Response, jsonify, render_template, request

from . import db, rules, trades
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


def _dashboard_auth_ok(app):
    password = app.config["DASHBOARD_PASSWORD"]
    if not password:
        return True
    auth = request.authorization
    return bool(auth and auth.password and hmac.compare_digest(auth.password, password))


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)
    if not app.config["WEBHOOK_SECRET"]:
        log.warning("WEBHOOK_SECRET is not set: webhook accepts unauthenticated requests")
    db.init_app(app)

    @app.before_request
    def protect_dashboard():
        # The webhook has its own secret; /health stays open for uptime checks.
        if request.endpoint in ("webhook", "health", "static"):
            return None
        if not _dashboard_auth_ok(app):
            return Response("Login required", 401,
                            {"WWW-Authenticate": 'Basic realm="MS Break Assistant"'})

    @app.post("/webhook")
    def webhook():
        payload = _read_payload()
        if not _secret_ok(app, payload):
            return jsonify(status="error", error="invalid secret"), 401
        try:
            signal = parse_signal(payload)
        except SignalError as e:
            return jsonify(status="error", error=str(e)), 400

        reason = rules.check_signal(rules.day_status())
        if reason:
            trades.record_signal(signal, "rejected", reason=reason)
            log.info("Rejected %s signal: %s", signal.direction, reason)
            # 200 so TradingView does not treat it as a delivery failure.
            return jsonify(status="ok", accepted=False, reason=reason)

        trade_id = trades.open_trade(signal)
        trades.record_signal(signal, "accepted", trade_id=trade_id)
        log.info("Accepted %s signal: %s", signal.direction, signal.raw)
        return jsonify(status="ok", accepted=True, trade=trades.get_trade(trade_id))

    @app.post("/api/trades/<int:trade_id>/result")
    def trade_result(trade_id):
        result = (request.get_json(silent=True) or {}).get("result")
        try:
            found = trades.set_result(trade_id, result)
        except ValueError as e:
            return jsonify(status="error", error=str(e)), 400
        if not found:
            return jsonify(status="error", error="trade not found"), 404
        return jsonify(status="ok", trade=trades.get_trade(trade_id))

    @app.post("/api/trades/<int:trade_id>/entry")
    def trade_entry(trade_id):
        try:
            entry = float((request.get_json(silent=True) or {})["entry"])
            found = trades.set_entry(trade_id, entry)
        except (KeyError, TypeError, ValueError) as e:
            return jsonify(status="error", error=f"invalid entry: {e}"), 400
        if not found:
            return jsonify(status="error", error="trade not found"), 404
        return jsonify(status="ok", trade=trades.get_trade(trade_id))

    @app.get("/api/state")
    def state():
        status = rules.day_status()
        return jsonify(status=status,
                       can_trade=rules.check_signal(status) is None,
                       block_reason=rules.check_signal(status),
                       trades=trades.trades_for_day(status["trading_day"]),
                       signals=trades.recent_signals(),
                       tp_points=app.config["TP_POINTS"],
                       sl_points=app.config["SL_POINTS"])

    @app.get("/api/trades")
    def list_trades():
        day = request.args.get("day") or trades.trading_day()
        return jsonify(day=day, trades=trades.trades_for_day(day))

    @app.get("/api/signals")
    def list_signals():
        return jsonify(signals=trades.recent_signals())

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html", market_tz=app.config["MARKET_TIMEZONE"])

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    return app
