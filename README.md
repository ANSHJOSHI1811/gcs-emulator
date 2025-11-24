# GCS Emulator - LocalStack for Google Cloud Storage

A production-ready **Google Cloud Storage (GCS) emulator** that runs locally, similar to LocalStack but specifically designed for GCP Storage. Built with Flask and PostgreSQL, it provides full compatibility with the official Google Cloud Storage Python SDK.

## ✨ Features

- ✅ **Full GCS API v1 Compatibility** - All 9 core endpoints implemented
- ✅ **Official SDK Support** - Works with `google-cloud-storage` library
- ✅ **PostgreSQL Database** - Persistent metadata storage
- ✅ **File Storage** - Local filesystem for object storage
- ✅ **Mock Authentication** - No real GCP credentials needed
- ✅ **Prefix & Delimiter** - Folder simulation support
- ✅ **Hash Verification** - MD5 and CRC32C checksums
- ✅ **Production-Ready** - Alembic migrations, error handling, logging

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 17
- pip/virtualenv

### 2. Installation

```bash
# Clone repository
git clone https://github.com/ANSHJOSHI1811/gcs-emulator.git
cd gcs-emulator

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Start PostgreSQL service (Windows)
Get-Service postgresql-x64-17 | Start-Service

# Create database and user
psql -U postgres
CREATE DATABASE gcs_emulator;
CREATE USER gcs_user WITH PASSWORD 'gcs_password';
GRANT ALL PRIVILEGES ON DATABASE gcs_emulator TO gcs_user;
\q

# Run migrations
flask db upgrade
```

### 4. Start Emulator

```bash
python run.py
```

Server starts at `http://localhost:8080`

### 5. Use with SDK

```python
import os
from google.cloud import storage
from google.auth.credentials import AnonymousCredentials

# Point SDK to emulator
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'

# Use SDK normally (no real GCP account needed!)
client = storage.Client(project='test-project', credentials=AnonymousCredentials())

# Create bucket
bucket = client.create_bucket('my-bucket', location='US')

# Upload file
blob = bucket.blob('hello.txt')
blob.upload_from_string('Hello World!')

# Download file
content = blob.download_as_text()
print(content)  # "Hello World!"
```

## 📚 API Endpoints

All endpoints follow GCS API v1 specification:

### Buckets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/storage/v1/b?project=X` | List buckets |
| POST | `/storage/v1/b?project=X` | Create bucket |
| GET | `/storage/v1/b/{bucket}` | Get bucket metadata |
| DELETE | `/storage/v1/b/{bucket}` | Delete bucket (must be empty) |

### Objects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/storage/v1/b/{bucket}/o` | List objects |
| POST | `/storage/v1/b/{bucket}/o?name=X` | Upload object |
| GET | `/storage/v1/b/{bucket}/o/{object}` | Get object metadata |
| GET | `/storage/v1/b/{bucket}/o/{object}?alt=media` | Download object |
| DELETE | `/storage/v1/b/{bucket}/o/{object}` | Delete object |

## 🧪 Testing

### Quick Test with SDK

```bash
python example_sdk_usage.py
```

### Full Integration Test Suite

```bash
python test_sdk_integration.py
```

Tests include:
- ✅ SDK connection
- ✅ Bucket CRUD operations
- ✅ Object upload/download
- ✅ Prefix & delimiter listing
- ✅ Error handling (404, 409, 400)

### Direct HTTP Tests (Postman)

```bash
# List buckets
GET http://localhost:8080/storage/v1/b?project=test-project

# Create bucket
POST http://localhost:8080/storage/v1/b?project=test-project
Content-Type: application/json
{"name": "my-bucket", "location": "US"}

# Upload object
POST http://localhost:8080/storage/v1/b/my-bucket/o?name=test.txt
Content-Type: text/plain
<binary content>
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│         Google Cloud Storage SDK                │
│         (google-cloud-storage)                  │
└─────────────────────────────────────────────────┘
                      ↓
        STORAGE_EMULATOR_HOST=localhost:8080
                      ↓
┌─────────────────────────────────────────────────┐
│              Flask Application                  │
│   ┌─────────────────────────────────────┐      │
│   │  Handlers (buckets.py, objects.py)  │      │
│   └─────────────────────────────────────┘      │
│                     ↓                           │
│   ┌─────────────────────────────────────┐      │
│   │  Services (business logic)          │      │
│   └─────────────────────────────────────┘      │
│                     ↓                           │
│   ┌──────────────────────┬─────────────────┐   │
│   │  SQLAlchemy (ORM)    │  File Storage   │   │
│   └──────────────────────┴─────────────────┘   │
└─────────────────────────────────────────────────┘
            ↓                        ↓
    ┌──────────────┐      ┌──────────────────┐
    │  PostgreSQL  │      │  ./storage/      │
    │   Database   │      │  (local files)   │
    └──────────────┘      └──────────────────┘
```

## 📁 Project Structure

```
gcs-emulator/
├── app/
│   ├── __init__.py
│   ├── factory.py              # Flask app factory + SDK middleware
│   ├── config.py               # Configuration (SDK compatibility settings)
│   ├── db.py                   # Database initialization
│   ├── cli.py                  # CLI commands
│   ├── handlers/               # HTTP request handlers
│   │   ├── buckets.py          # Bucket endpoints
│   │   ├── objects.py          # Object endpoints
│   │   ├── health.py           # Health check
│   │   └── errors.py           # Error handlers
│   ├── services/               # Business logic
│   │   ├── bucket_service.py   # Bucket operations
│   │   ├── object_service.py   # Object operations
│   │   └── validation.py       # Input validation
│   ├── models/                 # SQLAlchemy models
│   │   ├── project.py
│   │   ├── bucket.py
│   │   └── object.py
│   ├── serializers/            # JSON serialization
│   └── utils/                  # Utilities (hashing, validators)
├── migrations/                 # Alembic database migrations
├── docs/                       # Documentation
│   └── SDK_INTEGRATION.md      # SDK integration guide
├── storage/                    # Local file storage (runtime)
├── test_sdk_integration.py     # Full SDK test suite
├── example_sdk_usage.py        # Quick SDK example
├── requirements.txt
├── run.py
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator

# Flask
FLASK_ENV=development
FLASK_APP=run.py
SECRET_KEY=dev-key-not-for-production

# SDK Compatibility
SDK_COMPATIBLE_MODE=true
MOCK_AUTH_ENABLED=true
STORAGE_EMULATOR_HOST=http://localhost:8080
```

### Database Credentials

- **Database**: `gcs_emulator`
- **User**: `gcs_user`
- **Password**: `gcs_password`
- **Admin**: `postgres` / `12345678`

## 🎯 Use Cases

### Local Development

```python
# No GCP account needed - perfect for local dev
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'
client = storage.Client(project='dev-project', credentials=AnonymousCredentials())
```

### Testing

```python
# Fast integration tests without cloud latency
def test_upload():
    bucket = client.create_bucket('test-bucket')
    blob = bucket.blob('test.txt')
    blob.upload_from_string('test data')
    assert blob.exists()
```

### CI/CD Pipelines

```yaml
# GitHub Actions example
services:
  postgres:
    image: postgres:17
  gcs-emulator:
    image: gcs-emulator:latest
    environment:
      STORAGE_EMULATOR_HOST: http://localhost:8080
```

### Cost Savings

- ❌ **Without Emulator**: Every test hits real GCS → API costs, egress fees
- ✅ **With Emulator**: Tests run locally → $0 cost, faster execution

## 📖 Documentation

- **[SDK Integration Guide](docs/SDK_INTEGRATION.md)** - Detailed SDK usage
- **[API Reference](docs/API_REFERENCE.md)** - All endpoints
- **[Architecture](docs/ARCHITECTURE.md)** - System design
- **[Database Schema](docs/DATABASE_SCHEMA.md)** - Tables and relationships

## 🚢 Deployment

### Docker (Coming Soon)

```bash
docker-compose up
```

### Production Server

```bash
gunicorn -w 4 -b 0.0.0.0:8080 "app:create_app()"
```

## 🔄 Switching to Real GCP

When ready for production, just remove emulator config:

```python
# Development (emulator)
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'
client = storage.Client(project='dev', credentials=AnonymousCredentials())

# Production (real GCP) - NO CODE CHANGES!
# Just remove the environment variable and use real credentials
client = storage.Client(project='prod')
```

## 🎓 Learning Resources

### How SDK Works

1. **Lifecycle**: SDK → OAuth2 token → HTTP request → Response parsing
2. **Transport**: REST API (HTTP/1.1 + JSON) by default
3. **Diversion**: `STORAGE_EMULATOR_HOST` overrides base URL

See **[SDK Technical Breakdown](docs/SDK_INTEGRATION.md#how-it-works)** for details.

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] More GCS features (IAM, signed URLs, versioning)
- [ ] gRPC support
- [ ] Performance optimization
- [ ] Docker containerization
- [ ] Additional SDKs (Java, Node.js, Go)

## 📝 License

MIT License - see LICENSE file

## 🙏 Credits

Built by [Ansh Joshi](https://github.com/ANSHJOSHI1811)

Inspired by [LocalStack](https://github.com/localstack/localstack) - the AWS emulator

## 🐛 Troubleshooting

### SDK still connects to real GCP

Set environment variable **before** importing SDK:

```python
import os
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'  # FIRST
from google.cloud import storage  # THEN
```

### Database connection errors

```bash
# Check PostgreSQL is running
Get-Service postgresql-x64-17

# Test connection
psql -U gcs_user -d gcs_emulator -h localhost
```

### Port 8080 already in use

```bash
# Change port in run.py
app.run(host='0.0.0.0', port=8081, debug=True)
```

## 📊 Project Status

- ✅ **Phase 1-3**: Project structure and skeleton code
- ✅ **Phase 4**: Database setup with Alembic
- ✅ **Phase 5**: All 9 API endpoints implemented
- ✅ **Phase 5.5**: SDK compatibility layer added
- ✅ **Code Quality**: Refactored for maintainability (22 helper methods)
- ⏭️ **Phase 6**: Comprehensive testing (unit/integration)
- ⏭️ **Phase 7**: Real GCP SDK integration testing
- ⏭️ **Phase 8**: Docker deployment

## 🔗 Links

- **Repository**: https://github.com/ANSHJOSHI1811/gcs-emulator
- **Issues**: https://github.com/ANSHJOSHI1811/gcs-emulator/issues
- **GCS Documentation**: https://cloud.google.com/storage/docs

---

**Made with ❤️ for developers who want to test GCS locally without cloud costs**
