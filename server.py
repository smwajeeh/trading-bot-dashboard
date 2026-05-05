from flask import Flask, request
import json
import os

app = Flask(__name__)

DATA_FILE = "data.json"

def save_signal(signal):
    data = {"signal": signal}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    signal = data.get("message")

    save_signal(signal)

    print(f"Received: {signal}")
    return {"status": "ok"}

@app.route("/")
def home():
    return "Webhook is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
