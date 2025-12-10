# Running GCP Emulator in WSL2

## Why WSL2?

Docker Desktop runs Docker Engine **inside WSL2**, not on Windows. For the Compute Service to work correctly with Docker containers, the backend should run in the same WSL2 environment where Docker Engine is running.

**Architecture:**
```
┌─────────────────────────────────────┐
│           Windows 11                │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ VSCode / Browser / Tools     │  │
│  └──────────────────────────────┘  │
│              ↕ HTTP                 │
│  ┌──────────────────────────────┐  │
│  │         WSL2 Ubuntu           │  │
│  │                               │  │
│  │  Flask Backend (port 8080)    │  │
│  │         ↕                     │  │
│  │  Docker Engine                │  │
│  │  └─ Compute Instances         │  │
│  │                               │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Prerequisites

- Windows 11 with WSL2 installed
- Docker Desktop for Windows (with WSL2 backend)
- Ubuntu 22.04+ in WSL2

## Quick Start

### 1. Open WSL2

```powershell
# From Windows PowerShell or Terminal
wsl
```

### 2. Navigate to Project

```bash
cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package
```

### 3. Set Up Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Start PostgreSQL (Choose One Option)

**Option A: Docker PostgreSQL (Recommended)**

```bash
docker run -d \
  --name gcp-postgres \
  --restart unless-stopped \
  -e POSTGRES_USER=gcs_user \
  -e POSTGRES_PASSWORD=gcs_password \
  -e POSTGRES_DB=gcs_emulator \
  -p 5432:5432 \
  -v gcp-postgres-data:/var/lib/postgresql/data \
  postgres:17
```

**Option B: Use Windows PostgreSQL**

See [WSL_POSTGRES_SETUP.md](./WSL_POSTGRES_SETUP.md) for configuration steps.

### 5. Run Database Migrations

```bash
python3 migrations/001_add_object_versioning.py
python3 migrations/002_add_compute_instances.py
```

### 6. Start Backend

```bash
# Quick start (recommended)
chmod +x run_wsl.sh
./run_wsl.sh

# OR manually
python3 run.py
```

Backend will start on: http://localhost:8080

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database (auto-detects Windows host IP in WSL2)
DATABASE_URL=postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator

# Storage (WSL2-native path for better performance)
STORAGE_PATH=/home/anshjoshi/gcp_emulator_storage

# Compute Service
COMPUTE_ENABLED=true
COMPUTE_NETWORK=gcs-compute-net
COMPUTE_PORT_MIN=30000
COMPUTE_PORT_MAX=40000
COMPUTE_SYNC_INTERVAL=10
```

### Storage Paths

**WSL2-native path (recommended for performance):**
```
/home/anshjoshi/gcp_emulator_storage
```

**Windows-accessible path (slower but accessible from Windows Explorer):**
```
/mnt/c/Users/ansh.joshi/gcp_emulator/storage
```

## Testing

### Verify Docker Connection

```bash
docker ps
```

Should show any running containers.

### Verify Backend Health

```bash
curl http://localhost:8080/health
```

Should return: `{"status": "healthy"}`

### Run Compute Service Tests

```bash
python3 test_compute_service.py
```

## Common Issues

### Docker Not Accessible

**Error:** `docker: Cannot connect to the Docker daemon`

**Solution:**
```bash
# Check Docker Desktop is running in Windows
# Verify Docker service in WSL2
sudo service docker status

# If not running, start it
sudo service docker start
```

### PostgreSQL Connection Failed

**Error:** `connection to server at "X.X.X.X", port 5432 failed`

**Solutions:**
1. If using Docker PostgreSQL: Ensure container is running (`docker ps`)
2. If using Windows PostgreSQL: See [WSL_POSTGRES_SETUP.md](./WSL_POSTGRES_SETUP.md)

### Port Already in Use

**Error:** `Address already in use: 8080`

**Solution:**
```bash
# Find process using port 8080
sudo lsof -i :8080

# Kill the process
kill -9 <PID>
```

### Storage Permission Issues

**Error:** `Permission denied` when creating buckets/objects

**Solution:**
```bash
# Use WSL2-native path instead of /mnt/c/
export STORAGE_PATH=/home/$USER/gcp_emulator_storage
mkdir -p $STORAGE_PATH
```

## Development Workflow

### Edit Code in VSCode

You can edit files from Windows VSCode:
- Install "Remote - WSL" extension
- Open project in WSL: `code /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package`
- VSCode will show "WSL: Ubuntu" in bottom-left corner

### Hot Reload

Flask has auto-reload enabled in development mode. Changes to Python files will automatically restart the server.

### Access from Windows

The backend running in WSL2 is accessible from Windows:
- Backend API: http://localhost:8080
- Frontend (if running separately): http://localhost:3000

WSL2 automatically forwards localhost ports to Windows.

## Performance Tips

1. **Use WSL2-native paths** for storage (not `/mnt/c/`)
2. **Keep project files in WSL2 filesystem** for faster I/O
3. **Use Docker volumes** instead of bind mounts when possible
4. **Disable antivirus** scanning of WSL2 filesystem

## Accessing Files from Windows

To access WSL2 files from Windows Explorer:

```
\\wsl$\Ubuntu\home\anshjoshi\gcp_emulator_storage
```

Or in PowerShell:
```powershell
cd \\wsl$\Ubuntu\home\anshjoshi\
```

## Stopping Services

```bash
# Stop backend (Ctrl+C in terminal)

# Stop Docker PostgreSQL
docker stop gcp-postgres

# Stop all compute instances
docker ps --filter name=gce- -q | xargs docker stop
```

## Production Deployment

For production, use Docker Compose:

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_USER: gcs_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: gcs_emulator
    volumes:
      - postgres-data:/var/lib/postgresql/data
    
  backend:
    build: .
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql://gcs_user:${POSTGRES_PASSWORD}@postgres:5432/gcs_emulator
      STORAGE_PATH: /app/storage
    volumes:
      - ./storage:/app/storage
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - postgres

volumes:
  postgres-data:
```

Start with:
```bash
docker-compose up -d
```

## Next Steps

- [Compute Service Documentation](./COMPUTE_SERVICE_PHASE1.md)
- [API Documentation](./API_REFERENCE.md)
- [PostgreSQL Setup Guide](./WSL_POSTGRES_SETUP.md)
