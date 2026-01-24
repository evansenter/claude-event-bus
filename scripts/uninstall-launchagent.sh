#!/bin/bash
# Uninstall the agent event bus LaunchAgent

set -e

PLIST_DEST="$HOME/Library/LaunchAgents/com.evansenter.agent-event-bus.plist"
LABEL="com.evansenter.agent-event-bus"

if [[ ! -f "$PLIST_DEST" ]]; then
    echo "LaunchAgent not installed."
    exit 0
fi

echo "Stopping service..."
launchctl unload "$PLIST_DEST" 2>/dev/null || true

echo "Removing plist..."
rm -f "$PLIST_DEST"

echo "Agent Event Bus LaunchAgent uninstalled."

# Also uninstall CLI
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/uninstall-cli.sh"

echo ""
echo "Note: Data remains at ~/.claude/contrib/agent-event-bus/"
osascript -e 'display notification "LaunchAgent uninstalled" with title "Agent Event Bus"' 2>/dev/null
