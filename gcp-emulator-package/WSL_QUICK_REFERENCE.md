# WSL Migration - Quick Reference Card

## 🚀 Start Backend (from Windows PowerShell)

```powershell
cd C:\Users\ansh.joshi\gcp_emulator\gcp-emulator-package
wsl bash -c "PYTHONPATH=/mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package python3 run.py"
```

Expected: `Starting GCS Emulator on http://127.0.0.1:8080`

## ✅ Verify It Works (from Windows PowerShell)

```powershell
# Health check
wsl curl http://localhost:8080/health

# Docker
wsl docker ps

# PostgreSQL
wsl docker exec gcp-postgres pg_isready -U gcs_user
```

## 📁 Storage Directory

```bash
# Location (Linux path only)
/home/anshjoshi/gcs_emulator_storage

# View contents
wsl ls -la /home/anshjoshi/gcs_emulator_storage
```

## 🐳 Docker Commands (from PowerShell)

```powershell
# List containers
wsl docker ps

# Check PostgreSQL
wsl docker ps --filter "name=gcp-postgres"

# View logs
wsl docker logs gcp-postgres

# Execute SQL
wsl docker exec gcp-postgres psql -U gcs_user -d gcs_emulator -c "SELECT version();"

# Start/Stop
wsl docker start gcp-postgres
wsl docker stop gcp-postgres
```

## 🔧 Configuration Files

- **Backend**: `app/config.py` (has WSL detection)
- **Environment**: `.env` (Linux paths configured)
- **Storage**: `STORAGE_PATH=/home/anshjoshi/gcp_emulator_storage`

## 📊 Environment Variables

```env
# Database
DATABASE_URL=postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator

# Storage (LINUX ONLY - not Windows paths)
STORAGE_PATH=/home/anshjoshi/gcp_emulator_storage

# Compute Service
COMPUTE_ENABLED=true
COMPUTE_NETWORK=gcs-compute-net
COMPUTE_PORT_MIN=30000
COMPUTE_PORT_MAX=40000
```

## 🧪 Run Tests

```powershell
# Validation
wsl bash -c "cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package && \
  PYTHONPATH=/mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package \
  python3 tests/validate_wsl_migration.py"

# Unit tests
wsl bash -c "cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package && \
  python3 -m pytest tests/ -v"
```

## ⚡ Troubleshooting

| Issue | Solution |
|-------|----------|
| Docker not running | `wsl sudo service docker start` |
| PostgreSQL not found | `wsl docker ps` then `wsl docker start gcp-postgres` |
| Server won't start | Check PYTHONPATH, check if port 8080 is free |
| Storage permission denied | `wsl sudo chown anshjoshi:anshjoshi /home/anshjoshi/gcp_emulator_storage` |
| Tests fail | Run `validate_wsl_migration.py` to diagnose |

## 📝 Key Files

| File | Purpose | Status |
|------|---------|--------|
| `app/config.py` | WSL detection + Linux paths | ✅ Updated |
| `.env` | Environment configuration | ✅ Updated |
| `docs/WSL_MIGRATION_GUIDE.md` | Detailed guide | ✅ Created |
| `docs/WSL_MIGRATION_COMPLETE.md` | Summary report | ✅ Created |
| `tests/validate_wsl_migration.py` | Automated testing | ✅ Created |
| `start_wsl_server.sh` | Startup script | ✅ Created |

## 🎯 Architecture

```
Windows PowerShell
    ↓
wsl bash command
    ↓
WSL2 Ubuntu
    ├── Python 3 + Flask :8080
    ├── Docker Engine
    │   ├── PostgreSQL :5432
    │   └── Compute instances :30000-40000
    └── Storage /home/anshjoshi/gcp_emulator_storage
```

## ✨ Features Ready

- ✅ GCS Storage (upload, download, multipart, versioning)
- ✅ Lifecycle Rules (automatic cleanup)
- ✅ Docker Integration (native socket access)
- ✅ Compute Service (container management)
- ✅ Linux-native (no Windows dependencies)

## 📚 Full Documentation

- **Setup**: `docs/WSL_MIGRATION_GUIDE.md`
- **Complete Report**: `docs/WSL_MIGRATION_COMPLETE.md`
- **Backend README**: `README.md`

---

**TL;DR**: Backend runs in WSL. Docker works natively. Storage is at `/home/anshjoshi/gcs_emulator_storage`. Start with `python3 run.py`.
