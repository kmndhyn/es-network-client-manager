#!/bin/bash
cd "$(dirname "$0")" || exit 1
source venv/bin/activate

TS="/Applications/Tailscale.app/Contents/MacOS/Tailscale"
if [ ! -x "$TS" ]; then
    TS="$(command -v tailscale)"
fi

if [ -z "$TS" ]; then
    echo "Tailscale not found. Install it and sign in, then rerun this script."
    read -p "Press Enter to close..."
    exit 1
fi

# Publish the app on the tailnet as https://<machine>.<tailnet>.ts.net
# The app itself stays bound to 127.0.0.1 so it is not exposed on the local LAN.
"$TS" serve --bg 8000 >/dev/null 2>&1

NAME="$("$TS" status --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null)"
[ -z "$NAME" ] && NAME="$(scutil --get LocalHostName 2>/dev/null)"

echo ""
echo "ES Network Client Manager is now on your tailnet:"
echo ""
echo "    https://$NAME/"
echo ""
echo "Open that URL from any device on your tailnet (e.g. your PC)."
echo "Keep this window open while you use it. Press Ctrl+C to stop."
echo ""

uvicorn main:app --host 127.0.0.1 --port 8000
read -p "Press Enter to close..."
