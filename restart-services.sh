#!/bin/bash

# GCP Simulator - Service Restart Script
# This script restarts both frontend and backend services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║           🔄 Restarting GCP Simulator Services                      ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Stop services
"$SCRIPT_DIR/stop-services.sh"

echo ""
echo "⏳ Waiting 3 seconds..."
sleep 3
echo ""

# Start services
"$SCRIPT_DIR/start-services.sh"
