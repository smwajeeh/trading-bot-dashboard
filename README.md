# 📊 MS Break Trading Assistant

A lightweight trading assistant that connects TradingView alerts to a real-time dashboard for managing trades, enforcing rules, and improving discipline.

This tool is designed for traders using a **1-minute Market Structure Break (MSB) scalping strategy** with fixed TP/SL and strict daily risk rules.

> It does **not** place orders. It tells you when a signal is valid, where your TP/SL are, and when to stop for the day.

---

## 🚀 Features

- 📡 Receive TradingView signals via a secret-protected webhook
- 📈 Display LONG / SHORT trade alerts with sound + browser notification
- 🎯 Fixed TP/SL levels calculated from the entry (100 TP / 50 SL by default)
- 🧠 Enforce trading rules:
  - Only inside the trading window (open + 15 min → open + 2 h, New York time, weekdays)
  - Stop after **2 losses**
  - Stop after **1 win**
  - One trade at a time
- 📊 Track wins and losses per trading day (SQLite, survives restarts)
- ⚠️ Visual STOP warning system
- 🔒 Optional dashboard password
- ☁️ Cloud deployable (Fly.io)

---

## 🧠 Strategy Logic

- Timeframe: **1-minute**
- Market: **Nasdaq (MNQ / US100)**
- Entry: Market Structure Break (MSB)
- Trading Window:
  - First **2 hours** after market open (09:30–11:30 ET)
  - Ignore first **15-minute manipulation candle** (signals before 09:45 ET are rejected)

### Risk Management:
- Take Profit: **+100 points**
- Stop Loss: **-50 points**
- Daily rules:
  - ❌ Stop after 2 losses
  - ✅ Stop after 1 win

All of these are configurable (see [Configuration](#-configuration)).

---

## 🧱 Architecture

```
TradingView alert ──POST /webhook──▶ Flask app (gunicorn)
                                      │  1. check secret
                                      │  2. parse LONG/SHORT + price
                                      │  3. apply rules (window, daily stop, open trade)
                                      │  4. log signal; open trade with TP/SL if accepted
                                      ▼
                                   SQLite (DATA_DIR/assistant.db)
                                      ▲
Browser dashboard ──GET /api/state (every 3s)──┘
                  ──POST /api/trades/<id>/result  (win / loss / void)
                  ──POST /api/trades/<id>/entry   (set / correct fill price)
```

| File | Purpose |
|---|---|
| `server.py` | Entry point (`server:app` for gunicorn) |
| `assistant/__init__.py` | App factory and HTTP routes |
| `assistant/signals.py` | Parses TradingView payloads into LONG/SHORT signals |
| `assistant/rules.py` | Trading window and daily stop rules |
| `assistant/trades.py` | Storing signals and trades, TP/SL calculation |
| `assistant/db.py` | SQLite schema and connection handling |
| `assistant/templates/dashboard.html` | The dashboard (plain HTML + JS, no build step) |
| `tests/` | pytest suite |

### How a day works

1. A signal arrives. If it is outside the window, the daily stop has been hit, or a trade is already open, it is **rejected** and logged with the reason (visible on the dashboard).
2. Otherwise a trade opens. The dashboard beeps and shows entry, TP and SL. If the alert had no price, type your fill price to get the levels; you can also correct the entry if your fill differed.
3. When the trade closes, click **Win**, **Loss**, or **Void** (not taken / cancelled; doesn't count toward the limits).
4. After 1 win or 2 losses the banner turns red: **STOP TRADING**. Everything resets the next trading day.

---

## ⚙️ Configuration

All settings are environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `WEBHOOK_SECRET` | *(empty)* | Secret TradingView must send. **Set this in production.** |
| `DASHBOARD_PASSWORD` | *(empty)* | Password for the dashboard (any username). Empty = no login. |
| `DATA_DIR` | `data` (`/data` in Docker) | Where the SQLite database is stored |
| `MARKET_TIMEZONE` | `America/New_York` | Timezone for the window and trading day |
| `MARKET_OPEN` | `09:30` | Market open time (HH:MM) |
| `SKIP_MINUTES` | `15` | Minutes after open to ignore |
| `WINDOW_MINUTES` | `120` | Window end, in minutes after open |
| `TP_POINTS` | `100` | Take-profit distance in points |
| `SL_POINTS` | `50` | Stop-loss distance in points |
| `MAX_WINS` | `1` | Stop after this many wins |
| `MAX_LOSSES` | `2` | Stop after this many losses |
| `PORT` | `8080` | HTTP port |

Market holidays and early closes are not detected; on those days, just don't trade.

---

## 📡 TradingView setup

1. Create an alert on your MSB indicator/strategy.
2. **Webhook URL:** `https://<your-app>.fly.dev/webhook`
3. **Message** (JSON is recommended so the price comes through):

   ```json
   {"secret": "YOUR_WEBHOOK_SECRET", "action": "LONG", "price": {{close}}, "ticker": "{{ticker}}"}
   ```

   Use a second alert with `"action": "SHORT"` for shorts. For strategies you can use
   `"action": "{{strategy.order.action}}"` (`buy`/`sell` are understood).

   Plain-text alerts also work (e.g. `MSB LONG`). Put the secret in the URL instead:
   `https://<your-app>.fly.dev/webhook?secret=YOUR_WEBHOOK_SECRET`. Plain-text alerts have no
   price, so you enter the fill on the dashboard.

---

## 💻 Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python server.py                     # http://localhost:8080
pytest                               # run the tests
```

Send a test signal:

```bash
curl -X POST localhost:8080/webhook -H 'Content-Type: application/json' \
     -d '{"action": "LONG", "price": 20000}'
```

(Outside the trading window it will be rejected. That's the rules working.)

---

## ☁️ Deploy to Fly.io

```bash
fly launch --no-deploy --copy-config     # pick a unique app name (updates fly.toml)
fly volumes create data --size 1         # persistent storage for the database
fly secrets set WEBHOOK_SECRET=$(openssl rand -hex 16) DASHBOARD_PASSWORD=choose-one
fly deploy
fly secrets list                         # WEBHOOK_SECRET goes into your TradingView alert
```

The machine is kept running (`auto_stop_machines = "off"`) so webhooks are never delayed by a cold start.

---

## 🔌 API

| Method & path | Auth | Description |
|---|---|---|
| `POST /webhook` | webhook secret | Receive a TradingView alert |
| `GET /` | dashboard password | Dashboard |
| `GET /api/state` | dashboard password | Today's status, trades, recent signals |
| `GET /api/trades?day=YYYY-MM-DD` | dashboard password | Trades for a day (default today) |
| `GET /api/signals` | dashboard password | Last 20 signals |
| `POST /api/trades/<id>/result` | dashboard password | `{"result": "win" \| "loss" \| "void"}` |
| `POST /api/trades/<id>/entry` | dashboard password | `{"entry": 20000.25}`: set fill, recompute TP/SL |
| `GET /health` | none | Health check |
