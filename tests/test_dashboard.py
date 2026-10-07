import base64

from assistant import create_app


def test_dashboard_renders(client):
    r = client.get("/")
    assert r.status_code == 200 and b"MS Break Assistant" in r.data


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_dashboard_password(tmp_path, clock):
    app = create_app({"DATA_DIR": str(tmp_path), "CLOCK": clock,
                      "WEBHOOK_SECRET": "s3cret", "DASHBOARD_PASSWORD": "pw"})
    c = app.test_client()
    assert c.get("/").status_code == 401
    assert c.get("/api/state").status_code == 401
    assert c.post("/api/trades/1/result", json={"result": "win"}).status_code == 401
    good = {"Authorization": "Basic " + base64.b64encode(b"me:pw").decode()}
    assert c.get("/", headers=good).status_code == 200
    # Webhook and health check are not behind the dashboard password.
    assert c.get("/health").status_code == 200
    assert c.post("/webhook", json={"secret": "s3cret", "action": "LONG"}).status_code == 200
