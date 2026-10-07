import pytest

from assistant.signals import SignalError, parse_signal


@pytest.mark.parametrize("payload,direction", [
    ({"action": "LONG"}, "LONG"),
    ({"action": "sell"}, "SHORT"),
    ({"message": "MSB Bullish break"}, "LONG"),
    ("MSB SHORT signal", "SHORT"),
])
def test_parse_direction(payload, direction):
    assert parse_signal(payload).direction == direction


def test_parse_price_and_ticker():
    s = parse_signal({"action": "LONG", "price": "18250.25", "ticker": "MNQ1!"})
    assert s.price == 18250.25 and s.ticker == "MNQ1!"


@pytest.mark.parametrize("payload", [{}, "", {"action": "long short"}, {"action": "hello"},
                                     {"action": "LONG", "price": "abc"}])
def test_parse_rejects_bad_payloads(payload):
    with pytest.raises(SignalError):
        parse_signal(payload)


def test_webhook_requires_secret(client):
    assert client.post("/webhook", json={"action": "LONG"}).status_code == 401
    assert client.post("/webhook", json={"action": "LONG", "secret": "nope"}).status_code == 401


def test_webhook_accepts_valid_signal(client):
    r = client.post("/webhook", json={"action": "LONG", "price": 100, "secret": "s3cret"})
    assert r.status_code == 200
    assert r.get_json()["signal"]["direction"] == "LONG"


def test_webhook_plain_text_with_query_secret(client):
    r = client.post("/webhook?secret=s3cret", data="MSB SHORT", content_type="text/plain")
    assert r.status_code == 200
    assert r.get_json()["signal"]["direction"] == "SHORT"


def test_webhook_bad_payload_is_400_not_500(client):
    r = client.post("/webhook", json={"secret": "s3cret", "action": "???"})
    assert r.status_code == 400
