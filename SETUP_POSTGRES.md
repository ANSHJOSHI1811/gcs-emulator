# PostgreSQL Setup Guide

## Option 1: Install Docker Desktop (Recommended)

### Step 1: Install Docker Desktop
1. Download from: https://www.docker.com/products/docker-desktop
2. Run installer and restart your computer
3. Open Docker Desktop and wait for it to start

### Step 2: Start PostgreSQL with Docker
```powershell
cd C:\Users\ansh.joshi\GCP_Localstack
docker-compose up -d postgres
```

### Step 3: Update .env file
```
DATABASE_URL=postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator
```

### Step 4: Run migrations
```powershell
C:/Users/ansh.joshi/GCP_Localstack/.venv/Scripts/python.exe -m flask db upgrade
```

### Step 5: Start the app
```powershell
C:/Users/ansh.joshi/GCP_Localstack/.venv/Scripts/python.exe -m flask run --host=0.0.0.0 --port=8080
```

---

## Option 2: Run Full Stack with Docker

### Build and start everything:
```powershell
docker-compose up --build
```

This starts:
- PostgreSQL on port 5432
- GCS Emulator on port 5000

Access: http://localhost:5000

---

## Option 3: Install PostgreSQL Directly (No Docker)

### Step 1: Download PostgreSQL
Download from: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
Install PostgreSQL 15 or higher

### Step 2: Create Database
Open pgAdmin or psql and run:
```sql
CREATE DATABASE gcs_emulator;
CREATE USER gcs_user WITH PASSWORD 'gcs_password';
GRANT ALL PRIVILEGES ON DATABASE gcs_emulator TO gcs_user;
```

### Step 3: Update .env
```
DATABASE_URL=postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator
```

### Step 4: Run migrations
```powershell
C:/Users/ansh.joshi/GCP_Localstack/.venv/Scripts/python.exe -m flask db upgrade
```

---

## Current Status

**Currently running:** SQLite (no installation needed)
- Database file: `gcs_emulator.db`
- Works fine for development/testing
- No Docker or PostgreSQL required

**To switch to PostgreSQL:** Follow Option 1, 2, or 3 above
