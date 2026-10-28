#!/bin/bash
cd "$(dirname "$0")" || exit 1
source venv/bin/activate

PORT=8000
TS="/Applications/Tailscale.app/Contents/MacOS/Tailscale"
[ -x "$TS" ] || TS="$(command -v tailscale 2>/dev/null)"

echo ""
echo "Client Manager: http://127.0.0.1:$PORT"

# Optional: publish on the tailnet too. Absent or unconfigured Tailscale is fine.
if [ -n "$TS" ] && "$TS" serve --bg $PORT >/dev/null 2>&1; then
    NAME="$("$TS" status --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null)"
    [ -n "$NAME" ] && echo "Also on your tailnet: https://$NAME/"
fi

echo ""
echo "Keep this window open while you use it. Press Ctrl+C to stop."
echo ""

uvicorn main:app --host 127.0.0.1 --port $PORT
read -p "Press Enter to close..."
