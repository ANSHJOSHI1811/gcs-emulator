# Compute Engine Guide

## Overview

The GCP Emulator includes a **Compute Engine** service that allows you to create and manage virtual machine instances backed by Docker containers. This provides a lightweight way to test compute workloads locally.

## Prerequisites

### 1. Docker Running in WSL

Make sure Docker is running in your WSL Ubuntu-24.04 distribution:

```powershell
# From Windows PowerShell
wsl -d Ubuntu-24.04 docker ps
```

You should see output showing running containers (at least the postgres container).

### 2. Backend Configuration

The backend is configured to use Docker via WSL. Check your `.env` file:

```bash
COMPUTE_ENABLED=true
COMPUTE_NETWORK=gcs-compute-net
COMPUTE_PORT_MIN=30000
COMPUTE_PORT_MAX=40000
COMPUTE_SYNC_INTERVAL=5
```

## Starting the Services

### Backend (Flask API)

From PowerShell in the `gcp-emulator-package` directory:

```powershell
# Option 1: Using WSL
wsl -d Ubuntu-24.04 bash -c "cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package && source .venv/bin/activate && python run.py"

# Option 2: Using the start script
.\start_backend.ps1
```

The backend will start on `http://localhost:8080`

### Frontend (React UI)

From PowerShell in the `gcp-emulator-ui` directory:

```powershell
npm run dev
```

The UI will start on `http://localhost:3000`

## Using Compute Engine

### Via UI

1. Navigate to `http://localhost:3000`
2. Click **Services** → **Compute Engine**
3. Click **Create Instance**
4. Fill in the details:
   - **Name**: e.g., `my-test-vm` (lowercase, numbers, hyphens only)
   - **Image**: Select from popular images or enter custom Docker image
   - **CPU**: 1-8 cores
   - **Memory**: 128-8192 MB
5. Click **Create Instance**

The instance will:
- Pull the Docker image if not available
- Create and start a container
- Update state to `running`
- Auto-refresh every 5 seconds

### Via API

#### Create Instance

```bash
curl -X POST http://localhost:8080/compute/instances \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-instance",
    "image": "alpine:latest",
    "cpu": 1,
    "memory": 512
  }'
```

#### List Instances

```bash
curl http://localhost:8080/compute/instances
```

#### Get Instance

```bash
curl http://localhost:8080/compute/instances/{instance-id}
```

#### Stop Instance

```bash
curl -X POST http://localhost:8080/compute/instances/{instance-id}/stop
```

#### Terminate Instance

```bash
curl -X POST http://localhost:8080/compute/instances/{instance-id}/terminate
```

## Instance States

- **pending**: Instance being created
- **running**: Container is running
- **stopping**: Stop operation in progress
- **stopped**: Container is stopped
- **terminated**: Container removed (final state)

State transitions:
- `pending` → `running` (on creation)
- `running` → `stopping` → `stopped` (on stop)
- `any` → `terminated` (on terminate)

## Popular Docker Images

### Linux Distributions
- `alpine:latest` - Minimal Linux (5MB)
- `ubuntu:22.04` - Ubuntu LTS
- `debian:latest` - Debian stable

### Application Servers
- `nginx:latest` - Web server
- `redis:latest` - In-memory database
- `postgres:latest` - PostgreSQL database
- `python:3.11` - Python runtime
- `node:18` - Node.js runtime

## Troubleshooting

### Backend Not Starting

1. Check if PostgreSQL is running:
   ```powershell
   wsl -d Ubuntu-24.04 docker ps | findstr postgres
   ```

2. Check backend logs for errors

3. Verify WSL distribution name:
   ```powershell
   wsl --list --verbose
   ```

### Instance Stuck in "pending"

1. Check Docker is accessible:
   ```powershell
   wsl -d Ubuntu-24.04 docker info
   ```

2. Check backend logs for Docker errors

3. Verify image exists or can be pulled:
   ```powershell
   wsl -d Ubuntu-24.04 docker pull alpine:latest
   ```

### Instance Not Starting

1. Check container logs:
   ```powershell
   wsl -d Ubuntu-24.04 docker logs {container-id}
   ```

2. Check if container exists:
   ```powershell
   wsl -d Ubuntu-24.04 docker ps -a | findstr gcs-compute
   ```

3. Check resource limits (CPU/memory)

### UI Not Showing Instances

1. Check backend is running: `http://localhost:8080/health`
2. Check browser console for errors
3. Verify API endpoint: `http://localhost:8080/compute/instances`

## Architecture

```
┌─────────────────────┐
│   React Frontend    │
│  (Port 3000)        │
└──────────┬──────────┘
           │ HTTP
           ▼
┌─────────────────────┐
│   Flask Backend     │
│  (Port 8080)        │
└──────────┬──────────┘
           │ Docker API
           ▼
┌─────────────────────┐
│   Docker Engine     │
│  (WSL Ubuntu)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Containers        │
│  (VM Instances)     │
└─────────────────────┘
```

## Features

✅ Create instances from Docker images  
✅ List all instances with filters  
✅ Get instance details  
✅ Stop running instances  
✅ Terminate instances  
✅ Auto-sync container states (5-second interval)  
✅ Resource limits (CPU, memory)  
✅ State machine enforcement  
✅ Thread-safe Docker operations  
✅ Real-time UI updates  

## Limitations (Phase 1)

- No networking configuration
- No disk volumes/mounts
- No SSH access
- No custom startup scripts
- No instance metadata service
- No autoscaling
- No load balancing

These features may be added in future phases.

## Next Steps

- **Phase 2**: Networking (VPC, subnets, firewall rules)
- **Phase 3**: Persistent disks and volumes
- **Phase 4**: Instance templates and managed instance groups
- **Phase 5**: Load balancing and autoscaling

## Support

For issues or questions, check:
1. Backend logs in `gcp-emulator-package/logs/`
2. Docker logs: `wsl -d Ubuntu-24.04 docker logs {container-id}`
3. Browser console errors
