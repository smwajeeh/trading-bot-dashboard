def test_signal_opens_trade_with_levels(client, send):
    trade = send("LONG", 20000).get_json()["trade"]
    assert (trade["entry"], trade["take_profit"], trade["stop_loss"]) == (20000, 20100, 19950)
    assert trade["trading_day"] == "2026-10-06" and trade["result"] is None
    client.post(f"/api/trades/{trade['id']}/result", json={"result": "void"})

    trade = send("SHORT", 20000).get_json()["trade"]
    assert (trade["take_profit"], trade["stop_loss"]) == (19900, 20050)


def test_signal_without_price_has_no_levels(send):
    trade = send("LONG", None).get_json()["trade"]
    assert trade["take_profit"] is None and trade["stop_loss"] is None


def test_mark_result(client, send):
    tid = send().get_json()["trade"]["id"]
    r = client.post(f"/api/trades/{tid}/result", json={"result": "win"})
    assert r.status_code == 200 and r.get_json()["trade"]["result"] == "win"
    assert client.post(f"/api/trades/{tid}/result", json={"result": "bad"}).status_code == 400
    assert client.post("/api/trades/999/result", json={"result": "win"}).status_code == 404


def test_lists(client, send):
    send()
    assert len(client.get("/api/trades").get_json()["trades"]) == 1
    assert client.get("/api/signals").get_json()["signals"][0]["status"] == "accepted"


def test_data_persists_across_restarts(tmp_path, clock, send):
    from assistant import create_app
    send()
    app2 = create_app({"DATA_DIR": str(tmp_path), "CLOCK": clock})
    assert len(app2.test_client().get("/api/trades").get_json()["trades"]) == 1
