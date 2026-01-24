#!/bin/bash
# Uninstall agent-event-bus-cli from ~/.local/bin

CLI_PATH="$HOME/.local/bin/agent-event-bus-cli"

if [[ ! -e "$CLI_PATH" && ! -L "$CLI_PATH" ]]; then
    echo "agent-event-bus-cli not installed."
    exit 0
fi

rm -f "$CLI_PATH"
echo "Removed agent-event-bus-cli from ~/.local/bin"
