#!/bin/bash
cd "$(dirname "$0")" || exit 1

VENV_DIR=".venv"
PYTHON="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"
REQ="requirements.txt"
PORT=8000
HOST="127.0.0.1"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Installing dependencies..."
"$PIP" install -r "$REQ" --quiet

echo ""
echo "Client Manager: http://$HOST:$PORT"

TS=""
if [ -x "/Applications/Tailscale.app/Contents/MacOS/Tailscale" ]; then
    TS="/Applications/Tailscale.app/Contents/MacOS/Tailscale"
elif command -v tailscale >/dev/null 2>&1; then
    TS="$(command -v tailscale)"
fi

if [ -n "$TS" ]; then
    "$TS" serve --bg $PORT >/dev/null 2>&1 || true
    NAME="$("$TS" status --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null)"
    if [ -n "$NAME" ]; then
        echo "Also on your tailnet: https://$NAME/"
    fi
fi

echo ""
echo "Keep this window open. Press Ctrl+C to stop."
echo ""

"$PYTHON" -m uvicorn main:app --host "$HOST" --port "$PORT"
read -p "Press Enter to close..."
