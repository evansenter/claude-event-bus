#!/bin/bash
# Run event bus in development mode (foreground, auto-reload)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
source .venv/bin/activate

echo "Starting event bus in dev mode (Ctrl+C to stop)..."
echo "Add to Claude Code: claude mcp add --transport http --scope user event-bus http://127.0.0.1:8080/mcp"
echo ""

uvicorn event_bus.server:mcp.http_app --host 127.0.0.1 --port 8080 --reload --factory
