from datetime import timedelta

import pytest


def bar(client, high=None, low=None, price=None, **extra):
    body = {"secret": "s3cret", "event": "price", **extra}
    for k, v in (("high", high), ("low", low), ("price", price)):
        if v is not None:
            body[k] = v
    return client.post("/webhook", json=body)


def later(clock, seconds=60):
    clock.now += timedelta(seconds=seconds)


@pytest.mark.parametrize("direction,high,low,result,exit_price", [
    ("LONG", 20100, 19990, "win", 20100),    # TP 20100 touched
    ("LONG", 20050, 19950, "loss", 19950),   # SL 19950 touched
    ("LONG", 20100, 19950, "loss", 19950),   # both in one bar -> conservative loss
    ("SHORT", 20010, 19900, "win", 19900),
    ("SHORT", 20050, 19990, "loss", 20050),
])
def test_bar_closes_trade(client, clock, send, direction, high, low, result, exit_price):
    send(direction, 20000)
    later(clock)
    closed = bar(client, high, low).get_json()["closed"]
    assert (closed["result"], closed["exit_price"]) == (result, exit_price)
    assert closed["closed_by"] == ("auto-tp" if result == "win" else "auto-sl")


def test_bar_inside_range_keeps_trade_open(client, clock, send):
    send("LONG", 20000)
    later(clock)
    r = bar(client, 20090, 19960).get_json()
    assert r["closed"] is None and r["note"] == "TP/SL not reached"


def test_bar_right_after_entry_is_ignored(client, clock, send):
    send("LONG", 20000)
    later(clock, 5)
    assert "just opened" in bar(client, 20200, 19800).get_json()["note"]
    later(clock, 60)
    assert bar(client, 20200, 20010).get_json()["closed"]["result"] == "win"


def test_bar_with_only_price(client, clock, send):
    send("SHORT", 20000)
    later(clock)
    assert bar(client, price=19899).get_json()["closed"]["result"] == "win"


def test_bar_without_entry_price_does_nothing(client, clock, send):
    send("LONG", None)
    later(clock)
    assert bar(client, 30000, 10000).get_json()["closed"] is None


def test_auto_close_triggers_daily_stop(client, clock, send):
    send("LONG", 20000)
    later(clock)
    bar(client, 20100, 20000)
    r = send().get_json()
    assert r["accepted"] is False and "target" in r["reason"]


@pytest.mark.parametrize("result,expected,exit_price", [("tp", "win", 20100), ("SL", "loss", 19950)])
def test_exit_event(client, send, result, expected, exit_price):
    send("LONG", 20000)
    r = client.post("/webhook", json={"secret": "s3cret", "event": "exit", "result": result})
    closed = r.get_json()["closed"]
    assert (closed["result"], closed["exit_price"], closed["closed_by"]) == (expected, exit_price, "alert")


def test_exit_event_uses_given_price(client, send):
    send("LONG", 20000)
    r = client.post("/webhook", json={"secret": "s3cret", "event": "exit", "result": "win", "price": 20105})
    assert r.get_json()["closed"]["exit_price"] == 20105


def test_event_errors(client, send):
    send()
    post = lambda body: client.post("/webhook", json={"secret": "s3cret", **body})
    assert post({"event": "exit", "result": "maybe"}).status_code == 400
    assert post({"event": "price"}).status_code == 400
    assert post({"event": "price", "high": "x", "low": 1}).status_code == 400
    assert post({"event": "dance"}).status_code == 400
    assert client.post("/webhook", json={"event": "price", "price": 1}).status_code == 401


def test_no_open_trade(client):
    assert bar(client, price=1).get_json() == {"status": "ok", "closed": None, "note": "no open trade"}


def test_price_events_are_not_logged_as_signals(client, clock, send):
    send()
    later(clock)
    bar(client, price=20010)
    assert len(client.get("/api/signals").get_json()["signals"]) == 1


def test_last_bar_in_state(client):
    bar(client, 20010, 19990, 20000)
    lb = client.get("/api/state").get_json()["last_bar"]
    assert (lb["high"], lb["low"], lb["price"]) == (20010, 19990, 20000)


def test_old_open_trade_not_closed_by_todays_bars(client, clock, send):
    send("LONG", 20000)
    later(clock, 24 * 3600)
    assert bar(client, 20500, 20400).get_json()["closed"] is None


def test_manual_close_records_closed_by(client, send):
    tid = send().get_json()["trade"]["id"]
    t = client.post(f"/api/trades/{tid}/result", json={"result": "loss"}).get_json()["trade"]
    assert t["closed_by"] == "manual"


def test_migrates_old_database(tmp_path, clock):
    import sqlite3
    from assistant import create_app
    from assistant.db import SCHEMA
    old = SCHEMA.replace(",\n    exit_price  REAL,\n    closed_by   TEXT                    -- manual / auto-tp / auto-sl / alert", "")
    with sqlite3.connect(tmp_path / "assistant.db") as conn:
        conn.executescript(old)
        assert "closed_by" not in {r[1] for r in conn.execute("PRAGMA table_info(trades)")}
    create_app({"DATA_DIR": str(tmp_path), "CLOCK": clock})
    with sqlite3.connect(tmp_path / "assistant.db") as conn:
        assert {"exit_price", "closed_by"} <= {r[1] for r in conn.execute("PRAGMA table_info(trades)")}
