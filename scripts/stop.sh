#!/bin/bash
# Stop the event bus server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/.event-bus.pid"

if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm "$PID_FILE"
        echo "Event bus stopped (PID $PID)"
    else
        rm "$PID_FILE"
        echo "Event bus was not running (stale PID file removed)"
    fi
else
    echo "Event bus is not running"
fi
