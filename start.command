#!/bin/bash
# Double-click (Mac) or run ./start.command (Mac/Linux) to start the MS Break Assistant.
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Get it from https://www.python.org/downloads/ and run this again."
  read -r -p "Press Enter to close." ; exit 1
fi
if [ ! -d .venv ]; then
  echo "First run: setting up, this takes a minute..."
  python3 -m venv .venv || { read -r -p "Setup failed. Press Enter to close."; exit 1; }
fi
.venv/bin/python -m pip install -q -r requirements.txt || { read -r -p "Install failed. Press Enter to close."; exit 1; }
.venv/bin/python run_local.py "$@"
