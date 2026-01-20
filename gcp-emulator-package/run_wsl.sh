#!/bin/bash
#
# WSL2 Startup Script for GCP Emulator Backend
# This script starts the backend in WSL2 where Docker Engine is running
#

set -e  # Exit on error

echo "🚀 Starting GCP Emulator in WSL2..."

# Detect if running in WSL2
if grep -qi microsoft /proc/version; then
    echo "✅ Running in WSL2"
else
    echo "⚠️  Warning: Not running in WSL2. Docker may not work correctly."
fi

# Check Docker connectivity
echo "🐳 Checking Docker connection..."
if docker ps &> /dev/null; then
    echo "✅ Docker is accessible"
else
    echo "❌ Docker is not accessible. Please ensure Docker Desktop is running."
    exit 1
fi

# Create storage directory if it doesn't exist
STORAGE_DIR="${STORAGE_PATH:-/home/$USER/gcp_emulator_storage}"
echo "📦 Using storage directory: $STORAGE_DIR"
mkdir -p "$STORAGE_DIR"

# Check PostgreSQL connectivity
DB_HOST="${DATABASE_HOST:-$(grep nameserver /etc/resolv.conf | awk '{print $2}')}"
echo "🗄️  Testing PostgreSQL connection to $DB_HOST:5432..."
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/$DB_HOST/5432" 2>/dev/null; then
    echo "✅ PostgreSQL is accessible"
else
    echo "❌ PostgreSQL is not accessible at $DB_HOST:5432"
    echo ""
    echo "Please ensure PostgreSQL is configured to accept connections from WSL2."
    echo "See: https://github.com/ANSHJOSHI1811/gcs-emulator/blob/gcp_compute/docs/WSL_POSTGRES_SETUP.md"
    echo ""
    echo "Or use Docker PostgreSQL instead:"
    echo "  docker run -d --name gcp-postgres -e POSTGRES_USER=gcs_user -e POSTGRES_PASSWORD=gcs_password -e POSTGRES_DB=gcs_emulator -p 5432:5432 postgres:17"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if dependencies are installed
if ! python3 -c "import docker" &> /dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Run database migrations
echo "🗄️  Running database migrations..."
if [ -f "migrations/001_add_object_versioning.py" ]; then
    python3 migrations/001_add_object_versioning.py || echo "⚠️  Migration 001 already applied or failed"
fi
if [ -f "migrations/002_add_compute_instances.py" ]; then
    python3 migrations/002_add_compute_instances.py || echo "⚠️  Migration 002 already applied or failed"
fi

# Start the backend
echo "🌟 Starting Flask backend..."
echo "📍 API: http://localhost:8080"
echo "📊 Health: http://localhost:8080/health"
echo ""
python3 run.py
