#!/bin/bash

# GCP Simulator - Service Shutdown Script
# This script stops both frontend and backend services

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║           🛑 Stopping GCP Simulator Services                        ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Stop backend
BACKEND_PID=$(pgrep -f 'python.*run.py')
if [ -n "$BACKEND_PID" ]; then
    echo "🔧 Stopping Backend API Server (PID: $BACKEND_PID)..."
    kill $BACKEND_PID
    echo "   ✅ Backend stopped"
else
    echo "   ℹ️  Backend is not running"
fi

# Stop frontend
FRONTEND_PID=$(pgrep -f 'npm run dev')
if [ -n "$FRONTEND_PID" ]; then
    echo "🎨 Stopping Frontend UI Server (PID: $FRONTEND_PID)..."
    pkill -f 'npm run dev'
    pkill -f 'vite'
    echo "   ✅ Frontend stopped"
else
    echo "   ℹ️  Frontend is not running"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "✅ All services stopped"
echo "════════════════════════════════════════════════════════════════════════"
