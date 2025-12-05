# GCS Emulator

A production-ready **Google Cloud Storage (GCS) emulator** that runs locally. Built with Flask and PostgreSQL for the backend, and React with TypeScript for the frontend UI.

## 📁 Project Structure

```
gcp-emulator/
│
├── gcp-emulator-ui/              # React Frontend Application
│   ├── src/                      # TypeScript source code
│   ├── public/                   # Static assets
│   ├── package.json              # Node dependencies
│   └── vite.config.ts            # Vite configuration
│
└── gcp-emulator-package/         # Python Backend Emulator
    ├── app/                      # Flask application
    ├── tests/                    # Test suite
    ├── storage/                  # Object storage
    ├── migrations/               # Database migrations
    ├── docs/                     # Documentation
    ├── run.py                    # Server entry point
    ├── gcslocal.py               # CLI tool (gsutil-like)
    └── requirements.txt          # Python dependencies
```

## ✨ Features

### Backend (gcp-emulator-package)
- ✅ Full GCS API v1 Compatibility - All 9 core endpoints
- ✅ Official SDK Support - Works with `google-cloud-storage`
- ✅ PostgreSQL Database - Persistent metadata storage
- ✅ Object Versioning - Full generation support
- ✅ CLI Tool - `gcslocal` command (gsutil-like)
- ✅ Mock Authentication - No real GCP credentials needed
- ✅ Hash Verification - MD5 and CRC32C checksums

### Frontend (gcp-emulator-ui)
- ✅ Modern React UI with TypeScript
- ✅ Dashboard with storage statistics
- ✅ Bucket management interface
- ✅ Object browser with upload/download
- ✅ Object versioning viewer
- ✅ Real-time health monitoring

## 🚀 Quick Start

### Backend Setup

```powershell
# Navigate to backend
cd gcp-emulator-package

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (if not running)
Start-Service postgresql-x64-17

# Run the server
python run.py
```

Server will start at: `http://127.0.0.1:8080`

### Frontend Setup

```powershell
# Navigate to frontend
cd gcp-emulator-ui

# Install dependencies
npm install

# Start development server
npm run dev
```

UI will start at: `http://localhost:5173`

## 📖 Documentation

- **Backend Documentation**: See `gcp-emulator-package/README.md`
- **Setup Guide**: See `gcp-emulator-package/HOW_TO_RUN.md`
- **CLI Usage**: See `gcp-emulator-package/docs/CLI_CP.md`
- **Object Versioning**: See `gcp-emulator-package/docs/OBJECT_VERSIONING.md`
- **Frontend Documentation**: See `gcp-emulator-ui/README.md`

## 🔧 Usage with Google Cloud SDK

Set the environment variable to point to the emulator:

```powershell
# PowerShell
$env:STORAGE_EMULATOR_HOST = "http://127.0.0.1:8080"

# CMD
set STORAGE_EMULATOR_HOST=http://127.0.0.1:8080

# Linux/Mac
export STORAGE_EMULATOR_HOST=http://127.0.0.1:8080
```

Then use the official Google Cloud Storage Python SDK:

```python
from google.cloud import storage

# Will automatically use emulator
client = storage.Client(project="test-project")
bucket = client.create_bucket("my-bucket")
blob = bucket.blob("my-file.txt")
blob.upload_from_string("Hello, World!")
```

## 🛠️ CLI Tool (gcslocal)

Similar to `gsutil`, use `gcslocal` for command-line operations:

```powershell
# List buckets
python gcslocal.py ls

# Create bucket
python gcslocal.py mb gs://my-bucket

# Upload file
python gcslocal.py cp local-file.txt gs://my-bucket/

# Download file
python gcslocal.py cp gs://my-bucket/file.txt ./downloaded.txt
```

## 🧪 Testing

```powershell
cd gcp-emulator-package
pytest tests/
```

## 📊 API Endpoints

- `GET /health` - Health check
- `GET /storage/v1/b` - List buckets
- `POST /storage/v1/b` - Create bucket
- `GET /storage/v1/b/{bucket}` - Get bucket
- `DELETE /storage/v1/b/{bucket}` - Delete bucket
- `PATCH /storage/v1/b/{bucket}` - Update bucket
- `GET /storage/v1/b/{bucket}/o` - List objects
- `GET /storage/v1/b/{bucket}/o/{object}` - Get object metadata
- `POST /storage/v1/b/{bucket}/o` - Upload object
- `DELETE /storage/v1/b/{bucket}/o/{object}` - Delete object

## 🎯 Use Cases

- Local development without GCP costs
- CI/CD pipeline testing
- Integration testing
- Offline development
- Learning GCS API without real credentials

## 📝 License

MIT License

## 🤝 Contributing

Contributions welcome! Please read the contributing guidelines in each package.

## 🐛 Issues

Report issues on the GitHub repository.

---

**Built with ❤️ for local GCS development**
