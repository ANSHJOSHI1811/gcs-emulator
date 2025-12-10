# WSL2 Ubuntu Migration Guide

This guide covers the complete migration of the GCS Emulator backend from Windows to WSL2 Ubuntu with native Docker Engine support.

## Overview

**Migration Goal**: Run the entire GCS Emulator backend inside WSL2 Ubuntu with Docker Engine installed natively (not Docker Desktop).

**What Changed**:
- ✅ Backend runs fully inside WSL2 Ubuntu
- ✅ Docker Engine installed directly in WSL (docker.io package)
- ✅ Storage paths use Linux conventions (`/home/anshjoshi/gcp_emulator_storage`)
- ✅ Python SDK auto-detects Docker socket (`/var/run/docker.sock`)
- ✅ PostgreSQL runs in Docker container accessible from WSL
- ❌ No Windows Docker Desktop dependency
- ❌ No Windows path assumptions in code
- ❌ No DOCKER_HOST hacks needed

## Prerequisites

- **WSL2 with Ubuntu installed** (verified: 24.04 LTS)
- **Docker already running in WSL** (container `gcp-postgres` should be running)
- **Python 3.10+** installed in WSL
- **Sudo password**: 123456

## Architecture

```
Windows (PowerShell)
    ↓
WSL2 Ubuntu (Linux kernel + toolchain)
    ├── Python 3.x + Flask backend
    ├── Docker Engine (/var/run/docker.sock)
    │   ├── PostgreSQL container (port 5432)
    │   ├── Compute Service containers (ports 30000-40000)
    │   └── gcs-compute-net Docker network
    └── Storage directory (/home/anshjoshi/gcp_emulator_storage)
```

## Installation & Setup

### 1. Docker Engine is Already Installed

The Docker Engine has been pre-installed in WSL Ubuntu. Verify:

```bash
wsl docker ps
```

Expected output: Docker container list (including `gcp-postgres`)

### 2. Start Docker Daemon (First Time)

If Docker daemon is not running, start it:

```bash
wsl sudo service docker start
```

### 3. Add Your User to Docker Group

(Already done, but verify):

```bash
wsl id anshjoshi
# Should include: groups=1000(anshjoshi),999(docker)...
```

If not in docker group:
```bash
wsl sudo usermod -aG docker anshjoshi
wsl newgrp docker
```

### 4. Create Storage Directory

Storage directory already created. Verify:

```bash
wsl ls -la /home/anshjoshi/gcp_emulator_storage
# Should be: drwxr-xr-x 2 anshjoshi anshjoshi
```

### 5. PostgreSQL Container

PostgreSQL should already be running. Verify:

```bash
wsl docker ps --filter "name=gcp-postgres"
```

If not running:
```bash
wsl docker start gcp-postgres
```

To check PostgreSQL is accepting connections:
```bash
wsl docker exec gcp-postgres pg_isready -U gcs_user
# Expected: /var/run/postgresql:5432 - accepting connections
```

## Running the Backend Inside WSL

### Option 1: From Windows PowerShell (Recommended)

Run all commands from PowerShell - they execute inside WSL automatically:

```powershell
# Start Flask backend
cd C:\Users\ansh.joshi\gcp_emulator\gcp-emulator-package
wsl bash -c "cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package && \
  PYTHONPATH=/mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package \
  python3 run.py"
```

Expected output:
```
Starting GCS Emulator on http://127.0.0.1:8080
 * Running on http://127.0.0.1:8080
```

### Option 2: Inside WSL Terminal

Open WSL terminal and run:

```bash
cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package
export PYTHONPATH=/mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package
python3 run.py
```

### Option 3: Using Bash Script

A startup script is provided:

```bash
wsl bash ./gcp-emulator-package/run_wsl.sh
```

## Environment Variables

All environment variables are configured in `.env`:

```env
# Database (PostgreSQL in Docker)
DATABASE_URL=postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator

# Storage (Linux path only)
STORAGE_PATH=/home/anshjoshi/gcp_emulator_storage

# Compute Service
COMPUTE_ENABLED=true
COMPUTE_NETWORK=gcs-compute-net
COMPUTE_PORT_MIN=30000
COMPUTE_PORT_MAX=40000
COMPUTE_SYNC_INTERVAL=5
```

**Do NOT modify storage path to Windows paths** - they won't work inside WSL Python.

## Testing the Backend

### 1. Health Check

From PowerShell:
```powershell
# Wait for server to start, then:
curl http://localhost:8080/health
```

Expected: HTTP 200 with JSON response

### 2. Create Bucket

```powershell
curl -X POST http://localhost:8080/storage/v1/b `
  -H "Content-Type: application/json" `
  -d '{"project_id":"test-project", "name":"test-bucket"}'
```

### 3. Run Full Test Suite

```powershell
wsl bash -c "cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package && \
  PYTHONPATH=/mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package \
  python3 -m pytest tests/ -v"
```

## Docker Engine Inside WSL

Docker Engine is now running inside WSL, not Docker Desktop on Windows.

### Key Differences

| Aspect | Docker Desktop | WSL Docker |
|--------|---|---|
| Socket path | Windows npipe | `/var/run/docker.sock` |
| Detection | Via DOCKER_HOST env | Auto via `docker.from_env()` |
| Python SDK | Requires DOCKER_HOST hack | Works natively |
| Volume mounts | Windows paths | Linux paths only |
| Performance | Network overhead | Native Linux performance |

### Verify Docker Works

```bash
wsl docker images          # List images
wsl docker ps              # List running containers
wsl docker exec gcp-postgres pg_isready  # Test PostgreSQL
```

### Running Containers with Volume Mounts

All volume mounts MUST use Linux paths:

```bash
# ✅ CORRECT
wsl docker run -v /home/anshjoshi/gcp_emulator_storage:/data ubuntu bash

# ❌ WRONG (Windows path)
# Don't use: C:\Users\... or /mnt/c/Users/...
```

## Compute Service Preparation

The Compute Service is ready for WSL:

### 1. Network Created Automatically

Docker network `gcs-compute-net` is created automatically when needed:

```bash
wsl docker network ls
# Should show: gcs-compute-net (bridge driver)
```

### 2. Container Port Mapping Works

Ports 30000-40000 are reserved for compute instances:

```bash
# Example: Compute instance with public port 30001
wsl docker run -d \
  --name gcs-instance-i-abc123 \
  --network gcs-compute-net \
  -p 30001:22 \
  ubuntu
```

### 3. Volume Mounts for Instances

Instances can mount storage using Linux paths:

```bash
wsl docker run -d \
  --name gcs-instance-i-def456 \
  --network gcs-compute-net \
  -v /home/anshjoshi/gcp_emulator_storage:/mnt/storage \
  ubuntu
```

## File Path Compatibility

### Storage Service Audit

✅ **All file operations use `pathlib.Path`**:
- `object_service.py`: Uses `Path()` for all file I/O
- `resumable_upload_service.py`: Uses `Path()` with `.mkdir()`, `.read_bytes()`, `.write_bytes()`
- No hardcoded backslashes or Windows-specific logic

✅ **Storage paths are configurable**:
- Default: `/home/anshjoshi/gcp_emulator_storage`
- Via `STORAGE_PATH` environment variable
- Auto-detected as Linux path in WSL

✅ **No Windows dependencies**:
- No UNC paths (`\\server\share`)
- No drive letters (`C:\...`)
- No `os.sep` assumptions

### Validation

Run the file path validator:

```bash
wsl bash -c "python3 /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package/tests/validate_file_paths.py"
```

## Troubleshooting

### Docker Not Running

```bash
wsl sudo service docker start
wsl sudo usermod -aG docker $USER
wsl newgrp docker
```

### PostgreSQL Connection Refused

```bash
wsl docker ps --filter "name=gcp-postgres"
# If stopped:
wsl docker start gcp-postgres
```

### Storage Directory Permission Denied

```bash
# Fix ownership
wsl sudo chown -R anshjoshi:anshjoshi /home/anshjoshi/gcp_emulator_storage
wsl chmod 755 /home/anshjoshi/gcp_emulator_storage
```

### Python Import Errors

Ensure `PYTHONPATH` is set:
```bash
export PYTHONPATH=/mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package
python3 run.py
```

### Flask Server Port Already in Use

Kill existing process:
```bash
wsl lsof -i :8080
wsl kill -9 <PID>
```

## Quick Commands Reference

```bash
# Start services
wsl sudo service docker start

# Verify Docker
wsl docker ps
wsl docker exec gcp-postgres pg_isready -U gcs_user

# Start backend
wsl bash -c "cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package && \
  PYTHONPATH=/mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package \
  python3 run.py"

# Test health
curl http://localhost:8080/health

# Run tests
wsl bash -c "cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package && \
  PYTHONPATH=/mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package \
  python3 -m pytest tests/ -v"

# View logs
wsl tail -f /home/anshjoshi/gcp_emulator_storage/logs/*.log

# Check storage
wsl ls -la /home/anshjoshi/gcp_emulator_storage
```

## Migration Complete ✅

Your GCS Emulator backend is now fully running inside WSL2 Ubuntu with:

- ✅ Native Docker Engine (no Docker Desktop)
- ✅ Linux-native paths and file operations
- ✅ Full Compute Service support with volume mounts
- ✅ PostgreSQL database in Docker
- ✅ Proper permission management
- ✅ Cross-platform compatibility (backend in WSL, CLI from Windows)

All future development should assume Linux environment inside WSL.
