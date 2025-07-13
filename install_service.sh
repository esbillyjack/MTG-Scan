#!/bin/bash

# Magic Card Scanner - Service Installation Script

echo "🔧 Installing Magic Card Scanner as macOS Service..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Copy plist file to LaunchAgents directory
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS_DIR/com.magiccardscanner.server.plist"

echo "📁 Installing service to: $PLIST_FILE"

# Update the plist file with the correct path
sed "s|/Users/billjackson/Downloads/working/experiments/projects/magic-card-scanner|$SCRIPT_DIR|g" \
    "$SCRIPT_DIR/com.magiccardscanner.server.plist" > "$PLIST_FILE"

# Set correct permissions
chmod 644 "$PLIST_FILE"

# Load the service
echo "🚀 Loading service..."
launchctl load "$PLIST_FILE"

echo "✅ Service installed and started!"
echo "🌐 Access: http://localhost:8000"
echo ""
echo "To manage the service:"
echo "  Stop: launchctl unload $PLIST_FILE"
echo "  Start: launchctl load $PLIST_FILE"
echo "  Status: launchctl list | grep magiccardscanner"
echo "  Logs: tail -f $SCRIPT_DIR/logs/server.log" 