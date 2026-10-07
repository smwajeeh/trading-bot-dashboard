from datetime import datetime, timezone

import pytest

from assistant import create_app


class FakeClock:
    def __init__(self):
        # Tuesday 2026-10-06 10:00 New York time (14:00 UTC)
        self.now = datetime(2026, 10, 6, 14, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def app(tmp_path, clock):
    return create_app({"TESTING": True, "DATA_DIR": str(tmp_path), "WEBHOOK_SECRET": "s3cret",
                       "CLOCK": clock, "DASHBOARD_PASSWORD": "", "PRACTICE_MODE": False,
                       "BAR_GRACE_SECONDS": 30})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def send(client):
    def _send(action="LONG", price=20000, **extra):
        return client.post("/webhook", json={"secret": "s3cret", "action": action,
                                             "price": price, **extra})
    return _send
