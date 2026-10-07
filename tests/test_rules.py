from datetime import datetime, timezone

import pytest


def at(clock, y, mo, d, h, mi):
    # New York is UTC-4 in October 2026 (EDT)
    clock.now = datetime(y, mo, d, h + 4, mi, tzinfo=timezone.utc)


def close(client, resp, result):
    tid = resp.get_json()["trade"]["id"]
    assert client.post(f"/api/trades/{tid}/result", json={"result": result}).status_code == 200


@pytest.mark.parametrize("hm,accepted", [
    ((9, 30), False), ((9, 44), False), ((9, 45), True), ((11, 29), True), ((11, 30), False),
])
def test_trading_window(clock, send, hm, accepted):
    at(clock, 2026, 10, 6, *hm)
    assert send().get_json()["accepted"] is accepted


def test_weekend_rejected(clock, send):
    at(clock, 2026, 10, 10, 10, 0)  # Saturday
    r = send().get_json()
    assert r["accepted"] is False and "Weekend" in r["reason"]


def test_one_open_trade_at_a_time(send):
    assert send().get_json()["accepted"]
    r = send().get_json()
    assert r["accepted"] is False and "still open" in r["reason"]


def test_stop_after_one_win(client, send):
    close(client, send(), "win")
    r = send().get_json()
    assert r["accepted"] is False and "target" in r["reason"]


def test_stop_after_two_losses(client, send):
    close(client, send(), "loss")
    first = send()
    assert first.get_json()["accepted"]
    close(client, first, "loss")
    r = send().get_json()
    assert r["accepted"] is False and "losses" in r["reason"]


def test_void_does_not_count(client, send):
    close(client, send(), "void")
    assert send().get_json()["accepted"]


def test_rules_reset_next_day(clock, client, send):
    close(client, send(), "win")
    at(clock, 2026, 10, 7, 10, 0)
    assert send().get_json()["accepted"]


def test_rejected_signals_are_logged(client, clock, send):
    at(clock, 2026, 10, 6, 9, 35)
    send()
    sig = client.get("/api/signals").get_json()["signals"][0]
    assert sig["status"] == "rejected" and "Before trading window" in sig["reason"]


def test_state_endpoint(client, send):
    close(client, send(), "loss")
    s = client.get("/api/state").get_json()
    assert s["status"]["losses"] == 1 and s["can_trade"] is True
    assert s["status"]["window"]["state"] == "open"
