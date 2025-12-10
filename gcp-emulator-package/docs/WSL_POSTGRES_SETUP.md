# PostgreSQL Setup for WSL2

When running the backend in WSL2, PostgreSQL on Windows needs to be configured to accept connections from the WSL2 network.

## Quick Solution: Use Docker PostgreSQL (Recommended)

The easiest approach is to run PostgreSQL in Docker:

```bash
# Start PostgreSQL in Docker
docker run -d \
  --name gcp-postgres \
  --restart unless-stopped \
  -e POSTGRES_USER=gcs_user \
  -e POSTGRES_PASSWORD=gcs_password \
  -e POSTGRES_DB=gcs_emulator \
  -p 5432:5432 \
  -v gcp-postgres-data:/var/lib/postgresql/data \
  postgres:17

# Check if it's running
docker ps | grep gcp-postgres

# View logs
docker logs gcp-postgres
```

Then update your `.env` or export:
```bash
export DATABASE_URL="postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator"
```

## Alternative: Configure Windows PostgreSQL for WSL2

If you prefer to keep using Windows PostgreSQL:

### Step 1: Find PostgreSQL Config Files

Find your PostgreSQL data directory (usually `C:\Program Files\PostgreSQL\17\data\`).

### Step 2: Edit `postgresql.conf`

Open as Administrator and find the line:
```
#listen_addresses = 'localhost'
```

Change to:
```
listen_addresses = '*'
```

### Step 3: Edit `pg_hba.conf`

Add this line at the end:
```
# Allow connections from WSL2 network
host    all             all             172.16.0.0/12           md5
```

This allows connections from the entire WSL2 network range.

### Step 4: Restart PostgreSQL

In PowerShell (as Administrator):
```powershell
Restart-Service postgresql-x64-17
```

### Step 5: Test Connection from WSL2

```bash
# Get Windows host IP
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'

# Test connection (replace IP with your Windows host IP)
psql -h 10.255.255.254 -U gcs_user -d gcs_emulator
```

## Firewall Configuration

Windows Firewall may block PostgreSQL. Create a rule:

```powershell
# PowerShell (as Administrator)
New-NetFirewallRule -DisplayName "PostgreSQL WSL2" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow
```

## Troubleshooting

### Connection Refused

**Symptom**: `connection to server at "X.X.X.X", port 5432 failed: Connection refused`

**Solution**: PostgreSQL not listening on all interfaces. Check `postgresql.conf`.

### Connection Timed Out

**Symptom**: Connection hangs and times out

**Solution**: Windows Firewall blocking. Add firewall rule above.

### Authentication Failed

**Symptom**: `password authentication failed for user "gcs_user"`

**Solution**: Check `pg_hba.conf` has the correct authentication method (md5 or scram-sha-256).

## Why Docker PostgreSQL is Easier

✅ No Windows configuration needed
✅ Isolated from system PostgreSQL
✅ Easy to reset (just remove container)
✅ Portable across environments
✅ Automatic WSL2 connectivity
✅ Data persists in Docker volume

The only downside is you'll have two PostgreSQL instances (Windows + Docker), but they can coexist on different ports if needed.
