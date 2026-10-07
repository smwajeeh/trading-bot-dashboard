# 📊 MS Break Trading Assistant

A lightweight trading assistant that connects TradingView alerts to a real-time dashboard for managing trades, enforcing rules, and improving discipline.

This tool is designed for traders using a **1-minute Market Structure Break (MSB) scalping strategy** with fixed TP/SL and strict daily risk rules.

> It does **not** place orders or connect to a broker. It tells you when a signal is valid, where your TP/SL are, and when to stop for the day.

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
- 🤖 Automatic win/loss: a TradingView price feed closes the trade when TP or SL is hit
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

**Quick start:** double-click `practice.bat` (Windows) or `practice.command` (Mac). See [Run it on your computer](#-run-it-on-your-computer).

---

## 🧱 Architecture

```
TradingView alert ──POST /webhook──▶ Flask app (gunicorn)
                                      │  1. check secret
                                      │  2. parse LONG/SHORT + price
                                      │  3. apply rules (window, daily stop, open trade)
                                      │  4. log signal; open trade with TP/SL if accepted
TradingView price feed ─POST /webhook─▶│  5. close the open trade when a bar reaches TP/SL
                                      ▼
                                   SQLite (DATA_DIR/assistant.db)
                                      ▲
Browser dashboard ──GET /api/state (every 3s)──┘
                  ──POST /api/trades/<id>/result  (win / loss / void)
                  ──POST /api/trades/<id>/entry   (set / correct fill price)
```

| File | Purpose |
|---|---|
| `server.py` | Entry point for servers (`server:app` for gunicorn) |
| `run_local.py`, `start.*`, `practice.*` | One-click start on your own computer |
| `assistant/practice.py` | Practice-mode simulate buttons |
| `assistant/__init__.py` | App factory and HTTP routes |
| `assistant/signals.py` | Parses TradingView payloads into LONG/SHORT signals |
| `assistant/rules.py` | Trading window and daily stop rules |
| `assistant/exits.py` | Auto-closes trades from price-feed / exit alerts |
| `assistant/trades.py` | Storing signals and trades, TP/SL calculation |
| `assistant/db.py` | SQLite schema and connection handling |
| `assistant/templates/dashboard.html` | The dashboard (plain HTML + JS, no build step) |
| `tests/` | pytest suite |

### How a day works

1. A signal arrives. If it is outside the window, the daily stop has been hit, or a trade is already open, it is **rejected** and logged with the reason (visible on the dashboard).
2. Otherwise a trade opens. The dashboard beeps and shows entry, TP and SL. If the alert had no price, type your fill price to get the levels; you can also correct the entry if your fill differed.
3. When price reaches TP or SL, the [price feed](#-automatic-winloss-optional) closes the trade automatically and the dashboard beeps.
   Without a feed (or to override it) click **Win**, **Loss**, or **Void** (not taken / cancelled; doesn't count toward the limits).
4. After 1 win or 2 losses the banner turns red: **STOP TRADING**. Everything resets the next trading day.

---

## ⚙️ Configuration

All settings are environment variables, or lines in the `.env` file in the project folder:

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
| `BAR_GRACE_SECONDS` | `30` | Ignore price-feed bars this soon after a trade opens |
| `PRACTICE_MODE` | off | `1` ignores the trading window, stores data in `data-practice/`, adds simulate buttons |
| `PORT` | `8080` | HTTP port |

Market holidays and early closes are not detected; on those days, just don't trade.

---

## 💻 Run it on your computer

You need **Python 3.10 or newer** ([python.org/downloads](https://www.python.org/downloads/); on Windows tick
**"Add python.exe to PATH"** during install). Download the project (GitHub → **Code** → **Download ZIP**, then unzip it).

| | Windows | Mac |
|---|---|---|
| **Practice** (try it any time of day) | double-click `practice.bat` | double-click `practice.command` |
| **Real** (for live trading) | double-click `start.bat` | double-click `start.command` |

The first start takes a minute to install. Then your browser opens the dashboard at
<http://localhost:8080>. Keep the black window open while you trade; closing it stops the app.

On a Mac, if it says the file can't be opened, right-click it → **Open** → **Open** (only needed once).

### Practice mode

Practice mode ignores the 09:45–11:30 trading window and shows buttons that send the same alerts
TradingView would: **Send LONG/SHORT signal**, **Price hits TP/SL**, **Clear practice data**.
Practice trades are stored separately (`data-practice/`) and never mix with real ones.

### Connecting TradingView to your computer

TradingView can't reach `localhost`, so you give your computer a public web address with a free tunnel:

1. Sign up at [ngrok.com](https://ngrok.com), install it, and run the `ngrok config add-authtoken …` command it shows you.
2. On ngrok's dashboard open **Domains** and copy your free domain (e.g. `your-name.ngrok-free.app`).
3. With the app running, open a second terminal and run:
   `ngrok http 8080 --url=your-name.ngrok-free.app`
4. **Set a dashboard password**, because the dashboard is now reachable from the internet:
   open `.env` in the project folder, fill in `DASHBOARD_PASSWORD=`, and restart the app.
5. In your TradingView alerts use **Webhook URL** `https://your-name.ngrok-free.app/webhook` and the
   secret from the `WEBHOOK_SECRET=` line in `.env` (see [TradingView setup](#-tradingview-setup)).

TradingView only sends webhooks on its paid plans and asks you to turn on two-factor authentication first.

Your settings live in `.env` (created on first start, never uploaded to GitHub). Your trades live in `data/`.
Back that folder up if you care about the history.

### For developers

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
PRACTICE_MODE=1 python run_local.py
```

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

   Fire entry alerts **once per bar close** so the entry price matches the bar's close.

---

## 🤖 Automatic win/loss (optional)

Add a second alert that sends every 1-minute bar's high/low. When a bar reaches the open
trade's TP the trade is closed as a **win**; when it reaches SL, a **loss**.

1. In TradingView open the Pine Editor, paste this, and **Add to chart** on your 1-minute MNQ chart:

   ```pine
   //@version=5
   indicator("MSB price feed", overlay=true)
   secret = input.string("YOUR_WEBHOOK_SECRET", "Webhook secret")
   alert('{"secret":"' + secret + '","event":"price","high":' + str.tostring(high) +
         ',"low":' + str.tostring(low) + ',"price":' + str.tostring(close) + '}',
         alert.freq_once_per_bar_close)
   ```

2. Create an alert: **Condition:** `MSB price feed` → `Any alert() function call`,
   **Webhook URL:** `https://<your-app>.fly.dev/webhook`. Leave the message empty (the script supplies it).

The dashboard shows **Price feed live** while bars are arriving.

How it decides:

- A bar that touches **both** TP and SL counts as a **loss**: on a 1-minute bar there's no way to
  know which was hit first, so it takes the conservative side.
- Bars arriving within `BAR_GRACE_SECONDS` of the entry are ignored, because the signal bar can
  contain prices from before you entered.
- A trade with no entry price is never auto-closed; enter the fill first.
- Only today's open trade is ever closed. A trade left open from a previous day is not.
- Detection happens at bar close, so it lags the real TP/SL touch by up to a minute. That's fine for
  record-keeping; your broker's bracket order is what actually exits the position.

If your strategy already sends its own exit alerts, you can send those instead:
`{"secret": "...", "event": "exit", "result": "tp"}` (or `"sl"`, optionally with `"price"`).

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
| `POST /webhook` | webhook secret | Entry alert, or `"event": "price"` / `"event": "exit"` (see above) |
| `GET /` | dashboard password | Dashboard |
| `GET /api/state` | dashboard password | Today's status, trades, recent signals |
| `GET /api/trades?day=YYYY-MM-DD` | dashboard password | Trades for a day (default today) |
| `GET /api/signals` | dashboard password | Last 20 signals |
| `POST /api/trades/<id>/result` | dashboard password | `{"result": "win" \| "loss" \| "void"}` |
| `POST /api/trades/<id>/entry` | dashboard password | `{"entry": 20000.25}`: set fill, recompute TP/SL |
| `GET /health` | none | Health check |
