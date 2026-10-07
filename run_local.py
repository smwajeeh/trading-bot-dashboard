"""Start the assistant on this computer and open the dashboard.

    python run_local.py              # real mode
    python run_local.py --practice   # practice mode (no trading window, buttons to simulate alerts)

On first run it creates a .env file with a random webhook secret.
"""
import os
import secrets
import sys
import threading
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(ROOT, ".env")


def ensure_env_file():
    if os.path.exists(ENV_FILE):
        return
    with open(ENV_FILE, "w") as f:
        f.write(
            "# Settings for the MS Break Assistant. Edit, then restart the app.\n"
            f"WEBHOOK_SECRET={secrets.token_hex(16)}\n"
            "# Set a password if anyone else can reach this computer or you use a tunnel:\n"
            "DASHBOARD_PASSWORD=\n"
            "PORT=8080\n"
        )
    print(f"Created {ENV_FILE} with a new webhook secret.")


def main():
    ensure_env_file()
    if "--practice" in sys.argv:
        os.environ["PRACTICE_MODE"] = "1"

    sys.path.insert(0, ROOT)
    from assistant import create_app  # imported after PRACTICE_MODE is set

    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    url = f"http://localhost:{port}/"
    mode = "PRACTICE MODE" if app.config["PRACTICE_MODE"] else "real mode"

    print("\n" + "=" * 60)
    print(f"  MS Break Assistant is running ({mode})")
    print(f"  Dashboard:  {url}")
    print(f"  Webhook:    {url}webhook")
    print(f"  Secret:     {app.config['WEBHOOK_SECRET']}")
    print("  Stop it with Ctrl+C or by closing this window.")
    print("=" * 60 + "\n")

    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    from waitress import serve
    serve(app, host="127.0.0.1", port=port, threads=4)


if __name__ == "__main__":
    main()
