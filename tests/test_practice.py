from datetime import datetime, timezone

import pytest

from assistant import create_app


@pytest.fixture
def practice(tmp_path, clock):
    clock.now = datetime(2026, 10, 6, 22, 0, tzinfo=timezone.utc)  # 18:00 New York, window closed
    app = create_app({"DATA_DIR": str(tmp_path), "CLOCK": clock, "WEBHOOK_SECRET": "s3cret",
                      "DASHBOARD_PASSWORD": "", "PRACTICE_MODE": True, "BAR_GRACE_SECONDS": 0})
    return app.test_client()


def test_practice_endpoints_absent_normally(client):
    assert client.post("/api/practice/signal", json={"direction": "LONG"}).status_code == 404


def test_practice_flow_ignores_window(practice):
    r = practice.post("/api/practice/signal", json={"direction": "LONG"}).get_json()
    assert r["accepted"] and r["trade"]["entry"] == 20000
    assert practice.post("/api/practice/bar", json={"kind": "drift"}).get_json()["closed"] is None
    closed = practice.post("/api/practice/bar", json={"kind": "tp"}).get_json()["closed"]
    assert (closed["result"], closed["exit_price"]) == ("win", 20100)
    st = practice.get("/api/state").get_json()
    assert st["practice_mode"] and st["status"]["stopped"]


def test_practice_signal_uses_last_price(practice):
    practice.post("/api/practice/signal", json={"direction": "SHORT"})
    practice.post("/api/practice/bar", json={"kind": "sl"})  # closes at 20050
    practice.post("/api/practice/reset")
    st = practice.get("/api/state").get_json()
    assert st["trades"] == [] and st["signals"] == [] and st["last_bar"] is None


def test_practice_still_enforces_daily_stop(practice):
    for _ in range(2):
        practice.post("/api/practice/signal", json={"direction": "LONG"})
        practice.post("/api/practice/bar", json={"kind": "sl"})
    r = practice.post("/api/practice/signal", json={"direction": "LONG"}).get_json()
    assert r["accepted"] is False and "losses" in r["reason"]


def test_env_file_loading(tmp_path, monkeypatch):
    from assistant import config
    env = tmp_path / ".env"
    env.write_text('# comment\nFOO_TEST_KEY="bar"\nEXISTING_TEST_KEY=fromfile\n')
    monkeypatch.setenv("EXISTING_TEST_KEY", "fromenv")
    monkeypatch.delenv("FOO_TEST_KEY", raising=False)
    config._load_env_file(str(env))
    import os
    assert os.environ["FOO_TEST_KEY"] == "bar" and os.environ["EXISTING_TEST_KEY"] == "fromenv"
    monkeypatch.delenv("FOO_TEST_KEY")
