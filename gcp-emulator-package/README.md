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

# Google Cloud Storage Emulator

Simple, local Google Cloud Storage emulator built with Flask and PostgreSQL. Supports bucket/object CRUD, uploads/downloads, object metadata, object versioning (generations), and conditional preconditions. Includes a `gcslocal` CLI and works with the official `google-cloud-storage` SDK by setting `STORAGE_EMULATOR_HOST`.

## Requirements

- Python 3.10+
- PostgreSQL
- Virtual environment (recommended)

## Setup & Running Instructions

1. Clone repository
   ```powershell
   git clone https://github.com/ANSHJOSHI1811/gcs-emulator.git
   cd GCP_Localstack
   ```
2. Create and activate venv
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies
   ```powershell
   pip install -r requirements.txt
   ```
4. Configure environment variables
   ```powershell
   $env:DATABASE_URL = "postgresql://user:pass@localhost:5432/gcs_emulator"
   $env:STORAGE_EMULATOR_HOST = "http://127.0.0.1:8080"
   $env:FLASK_ENV = "development"
   ```
5. Run migrations
   ```powershell
   python -m migrations.001_add_object_versioning
   ```
6. Start server
   ```powershell
   python run.py
   ```

## CLI Usage (gcslocal)

Use the LocalStack-style CLI for bucket/object operations.

- Create bucket
  ```powershell
  python gcslocal.py mb gs://my-bucket
  ```
- List buckets
  ```powershell
  python gcslocal.py ls
  ```
- Upload (local → gs://)
  ```powershell
  python gcslocal.py cp C:\data\file.txt gs://my-bucket/path/file.txt
  ```
- Download (gs:// → local)
  ```powershell
  python gcslocal.py cp gs://my-bucket/path/file.txt C:\data\file.txt
  ```
- Delete object
  ```powershell
  python gcslocal.py rm gs://my-bucket/path/file.txt
  ```

## Using Python SDK

Set `STORAGE_EMULATOR_HOST` and use the official client.

```python
import os
from google.cloud import storage

os.environ["STORAGE_EMULATOR_HOST"] = "http://127.0.0.1:8080"
client = storage.Client(project="demo")

# Create bucket
bucket = client.create_bucket("my-bucket")

# Upload object (uses multipart upload)
blob = bucket.blob("path/file.txt")
blob.upload_from_filename("file.txt")
# Or upload from string
blob.upload_from_string("Hello, World!")

# Download object
content = blob.download_as_text()
blob.download_to_filename("downloaded.txt")

# List objects
for blob in bucket.list_blobs():
    print(blob.name)

# Delete object
blob.delete()
```

## Upload Types

The emulator supports two upload types:

### Media Upload (Simple)
Direct upload with object name in query parameter:
```http
POST /upload/storage/v1/b/{bucket}/o?uploadType=media&name={object}
Content-Type: text/plain

<file content>
```

### Multipart Upload (SDK Default)
Metadata + content in multipart/related format:
```http
POST /upload/storage/v1/b/{bucket}/o?uploadType=multipart
Content-Type: multipart/related; boundary=boundary123

--boundary123
Content-Type: application/json

{"name": "my-file.txt"}

--boundary123
Content-Type: text/plain

<file content>
--boundary123--
```

The Python SDK uses multipart upload by default for `blob.upload_from_filename()` and `blob.upload_from_string()`.

## Object Versioning

- Each new upload to the same object path creates a new `generation` (1, 2, ...).
- Download specific version via `?generation=N`.
- Delete specific version by passing `generation`.
- Preconditions on upload:
  - `ifGenerationMatch`: proceed only if current generation equals value.
  - `ifMetagenerationMatch`: proceed only if current metageneration equals value.

Examples (HTTP):
```http
PUT /upload/storage/v1/b/my-bucket/o?name=path/file.txt&ifGenerationMatch=2
Content-Type: application/octet-stream

<bytes>
```

Download a specific version:
```http
GET /storage/v1/b/my-bucket/o/path/file.txt?generation=2&alt=media
```

Delete a specific version:
```http
DELETE /storage/v1/b/my-bucket/o/path/file.txt?generation=2
```

## API Reference

Base: `http://127.0.0.1:8080`

### Bucket Operations
- Create: `POST /storage/v1/b?project=<project>`
- List: `GET /storage/v1/b?project=<project>`
- Get: `GET /storage/v1/b/<bucket>`
- Delete: `DELETE /storage/v1/b/<bucket>`

### Object Operations
- Upload (media): `POST /upload/storage/v1/b/<bucket>/o?uploadType=media&name=<path>`
- Upload (multipart): `POST /upload/storage/v1/b/<bucket>/o?uploadType=multipart`
- Download: `GET /storage/v1/b/<bucket>/o/<path>?alt=media`
- Download (SDK): `GET /download/storage/v1/b/<bucket>/o/<path>`
- Metadata: `GET /storage/v1/b/<bucket>/o/<path>`
- Delete: `DELETE /storage/v1/b/<bucket>/o/<path>`
- List: `GET /storage/v1/b/<bucket>/o`

### Versioning Query Parameters
- `generation` - Target specific version
- `ifGenerationMatch` - Proceed only if current generation equals value
- `ifGenerationNotMatch` - Proceed only if current generation differs
- `ifMetagenerationMatch` - Proceed only if metageneration equals value
- `ifMetagenerationNotMatch` - Proceed only if metageneration differs

## Running Tests

```powershell
pytest -v
```

Includes SDK transport mocking and end-to-end flows covering versioning and preconditions.

## Project Structure

```
app/
  handlers/        # HTTP endpoints
  services/        # Business logic incl. versioning
  models/          # SQLAlchemy models
  routes/          # Route registration
  logging/         # Logger & middleware
  utils/           # Hashing and helpers
docs/
  CLI_CP.md        # CLI documentation
  OBJECT_VERSIONING.md
tests/
  unit/, e2e/      # Test suites
```

## Future Work

- Signed URLs
- Resumable uploads
- Notifications (Pub/Sub)

## Status

**97 tests passing** - SDK bucket operations, CLI commands, multipart uploads, object versioning, and preconditions all fully functional.
- IAM/ACL
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
