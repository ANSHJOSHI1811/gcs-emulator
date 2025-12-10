# Quick Start Commands

## One-Time Setup (Run Once)

```bash
# 1. Enter WSL2
wsl

# 2. Navigate to project
cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package

# 3. Install system dependencies (if needed)
sudo apt update
sudo apt install -y python3-pip python3-venv

# 4. Create Python virtual environment
python3 -m venv .venv

# 5. Activate virtual environment
source .venv/bin/activate

# 6. Install Python dependencies
pip install -r requirements.txt

# 7. Start PostgreSQL in Docker (easiest option)
docker run -d \
  --name gcp-postgres \
  --restart unless-stopped \
  -e POSTGRES_USER=gcs_user \
  -e POSTGRES_PASSWORD=gcs_password \
  -e POSTGRES_DB=gcs_emulator \
  -p 5432:5432 \
  -v gcp-postgres-data:/var/lib/postgresql/data \
  postgres:17

# 8. Run migrations
python3 migrations/001_add_object_versioning.py
python3 migrations/002_add_compute_instances.py
```

## Daily Usage (Every Time)

```bash
# Option 1: Using the startup script (recommended)
wsl
cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package
chmod +x run_wsl.sh
./run_wsl.sh

# Option 2: Manual start
wsl
cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package
source .venv/bin/activate
python3 run.py
```

## Testing

```bash
# Test backend health
curl http://localhost:8080/health

# Test Compute Service
python3 test_compute_service.py

# List running compute instances
curl http://localhost:8080/compute/v1/projects/test-project/zones/us-central1-a/instances

# Check Docker containers
docker ps
```

## Useful Commands

```bash
# View backend logs (if running in background)
tail -f logs/app.log

# View Docker logs for a compute instance
docker logs <container-name>

# Stop all compute instances
docker ps --filter name=gce- -q | xargs docker stop

# Restart PostgreSQL
docker restart gcp-postgres

# View PostgreSQL logs
docker logs gcp-postgres

# Connect to PostgreSQL
docker exec -it gcp-postgres psql -U gcs_user -d gcs_emulator

# Check storage directory
ls -lah /home/anshjoshi/gcp_emulator_storage/
```

## Troubleshooting

```bash
# Check if Docker is accessible
docker ps

# Check if PostgreSQL is running
docker ps | grep postgres

# Test PostgreSQL connection
docker exec -it gcp-postgres pg_isready

# Check backend port
sudo lsof -i :8080

# View Docker networks
docker network ls

# Inspect compute network
docker network inspect gcs-compute-net

# Clean up stopped containers
docker container prune

# Clean up unused volumes
docker volume prune
```

## Stop Everything

```bash
# Stop backend (Ctrl+C if running in foreground)

# Stop PostgreSQL
docker stop gcp-postgres

# Stop all compute instances
docker ps --filter name=gce- -q | xargs docker stop

# Optional: Remove PostgreSQL container (data persists in volume)
docker rm gcp-postgres

# Optional: Remove all compute instance containers
docker ps -a --filter name=gce- -q | xargs docker rm
```

## Reset Everything (Nuclear Option)

```bash
# WARNING: This deletes all data!

# Stop and remove all containers
docker stop gcp-postgres
docker rm gcp-postgres
docker ps -a --filter name=gce- -q | xargs docker rm -f

# Remove volumes (this deletes all database data!)
docker volume rm gcp-postgres-data

# Remove storage directory
rm -rf /home/anshjoshi/gcp_emulator_storage/

# Then re-run the One-Time Setup steps above
```

## VS Code Integration

```bash
# Open project in VS Code from WSL
code /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package

# Or from Windows, install "Remote - WSL" extension and:
# 1. Open VS Code
# 2. Press F1
# 3. Type "WSL: Open Folder in WSL"
# 4. Navigate to /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package
```
