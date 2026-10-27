#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
open http://127.0.0.1:8000
uvicorn main:app --host 127.0.0.1 --port 8000
read -p "Press Enter to close..."
