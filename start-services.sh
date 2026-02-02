#!/bin/bash

# GCP Simulator - Service Startup Script
# This script starts both frontend and backend services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║           🚀 Starting GCP Simulator Services                        ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if services are already running
BACKEND_RUNNING=$(ps aux | grep -E "python.*run.py" | grep -v grep | wc -l)
FRONTEND_RUNNING=$(ps aux | grep -E "npm run dev" | grep -v grep | wc -l)

if [ $BACKEND_RUNNING -gt 0 ]; then
    echo "⚠️  Backend is already running (PID: $(pgrep -f 'python.*run.py'))"
else
    echo "🔧 Starting Backend API Server..."
    cd "$SCRIPT_DIR/gcp-stimulator-package"
    nohup python run.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "   ✅ Backend started (PID: $BACKEND_PID)"
    echo "   📝 Logs: logs/backend.log"
    cd "$SCRIPT_DIR"
fi

sleep 2

if [ $FRONTEND_RUNNING -gt 0 ]; then
    echo "⚠️  Frontend is already running (PID: $(pgrep -f 'npm run dev'))"
else
    echo "🎨 Starting Frontend UI Server..."
    cd "$SCRIPT_DIR/gcp-stimulator-ui"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "   📦 Installing dependencies (first time setup)..."
        npm install
    fi
    
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   ✅ Frontend started (PID: $FRONTEND_PID)"
    echo "   📝 Logs: logs/frontend.log"
    cd "$SCRIPT_DIR"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 3

# Check backend health
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "   ✅ Backend API:  http://localhost:8080 (healthy)"
else
    echo "   ⚠️  Backend API:  http://localhost:8080 (starting...)"
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "   ✅ Frontend UI:  http://localhost:3000 (ready)"
else
    echo "   ⏳ Frontend UI:  http://localhost:3000 (starting...)"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "📖 Access Points:"
echo "   • UI Dashboard:  http://localhost:3000"
echo "   • API Endpoint:  http://localhost:8080"
echo "   • API Health:    http://localhost:8080/health"
echo ""
echo "📊 Monitor Logs:"
echo "   • Backend:   tail -f logs/backend.log"
echo "   • Frontend:  tail -f logs/frontend.log"
echo ""
echo "🛑 Stop Services:"
echo "   • ./stop-services.sh"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
