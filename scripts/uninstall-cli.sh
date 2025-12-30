#!/bin/bash
# Uninstall event-bus-cli from ~/.local/bin

CLI_PATH="$HOME/.local/bin/event-bus-cli"

if [[ ! -e "$CLI_PATH" && ! -L "$CLI_PATH" ]]; then
    echo "event-bus-cli not installed."
    exit 0
fi

rm -f "$CLI_PATH"
echo "Removed event-bus-cli from ~/.local/bin"
