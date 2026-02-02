# 🔒 Security Implementation - Phase 1 Complete

## Overview

Phase 1 security features have been implemented to make GCP Stimulator production-ready. This includes authentication, rate limiting, input validation, HTTPS/TLS support, and security headers.

---

## 🎯 What's Been Implemented

### 1. ✅ Authentication System

**Location:** `app/middleware/auth_middleware.py`

**Features:**
- JWT token authentication
- API key authentication with SHA-256 hashing
- Three authentication modes:
  - `disabled` - No authentication (development)
  - `optional` - Track but don't require auth
  - `required` - Enforce authentication (production)
- Token expiration and validation
- Project-level access control

**Usage:**
```python
from app.middleware.auth_middleware import require_auth, require_project_access

@app.route('/api/resource')
@require_auth
def get_resource():
    user_info = request.user_info  # Auto-populated
    return {'user': user_info['user_id']}

@app.route('/api/projects/<project_id>/resources')
@require_project_access
def list_resources(project_id):
    # Automatically verifies user has access to project_id
    return {'resources': [...]}
```

### 2. ✅ API Key Management

**Location:** `app/routes/auth_routes.py`

**Endpoints:**
```bash
# Generate API key
POST /auth/api-keys
{
  "project_id": "my-project",
  "name": "My API Key",
  "expires_days": 365
}

# List API keys
GET /auth/api-keys?project_id=my-project

# Get API key details
GET /auth/api-keys/{key_id}

# Revoke API key
DELETE /auth/api-keys/{key_id}

# Generate JWT token
POST /auth/tokens
{
  "user_id": "user@example.com",
  "project_id": "my-project",
  "scopes": ["*"]
}

# Verify JWT token
POST /auth/tokens/verify
{"token": "eyJ..."}

# Get auth config
GET /auth/config
```

**API Key Format:**
```
gcps_<64-character-random-string>
```

**Using API Keys:**
```bash
curl -H "X-API-Key: gcps_abc123..." http://localhost:8080/api/resource
```

**Using JWT Tokens:**
```bash
curl -H "Authorization: Bearer eyJ..." http://localhost:8080/api/resource
```

### 3. ✅ Rate Limiting

**Location:** `app/middleware/rate_limiting.py`

**Features:**
- Sliding window rate limiting
- Per-client (IP or API key) limits
- Per-endpoint limits
- Redis-backed (optional) or in-memory
- Predefined tiers (Free, Basic, Premium, Admin)

**Usage:**
```python
from app.middleware.rate_limiting import rate_limit, rate_limit_tier

# Custom rate limit
@app.route('/api/resource')
@rate_limit(limit=100, window_seconds=60)
def get_resource():
    return {'data': [...]}

# Predefined tier
@app.route('/api/write')
@rate_limit_tier('write_ops')  # 20 req/min
def create_resource():
    return {'created': True}
```

**Response Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1643723456
```

**Rate Limit Tiers:**
- **FREE**: 10 requests/minute
- **BASIC**: 100 requests/minute
- **PREMIUM**: 1,000 requests/minute
- **ADMIN**: 10,000 requests/minute
- **WRITE_OPS**: 20 requests/minute
- **READ_OPS**: 200 requests/minute

### 4. ✅ Input Validation

**Location:** `app/middleware/input_validation.py`

**Features:**
- Schema-based validation
- SQL injection prevention
- XSS prevention
- Pattern matching (project IDs, bucket names, etc.)
- Length and range validation
- HTML sanitization

**Usage:**
```python
from app.middleware.input_validation import validate_request

@app.route('/api/projects/<project_id>/buckets', methods=['POST'])
@validate_request(
    body_schema={
        'name': {
            'required': True,
            'pattern': 'bucket_name',
            'min_length': 3,
            'max_length': 63
        },
        'location': {
            'required': True,
            'pattern': 'region'
        }
    },
    path_schema={
        'project_id': {
            'required': True,
            'pattern': 'project_id'
        }
    }
)
def create_bucket(project_id):
    data = request.get_json()
    # Data is already validated
    return {'bucket': data['name']}
```

**Validation Patterns:**
- `project_id`: `^[a-z][a-z0-9-]{4,28}[a-z0-9]$`
- `bucket_name`: `^[a-z0-9][a-z0-9-_.]{1,61}[a-z0-9]$`
- `instance_name`: `^[a-z][a-z0-9-]{0,61}[a-z0-9]$`
- `network_name`: `^[a-z][a-z0-9-]{0,61}[a-z0-9]$`
- `zone`: `^[a-z]+-[a-z]+\d-[a-z]$`
- `region`: `^[a-z]+-[a-z]+\d$`
- `email`: Standard email format
- `ip_address`: IPv4 format
- `cidr`: CIDR notation

### 5. ✅ HTTPS/TLS Support

**Location:** `app/middleware/tls_config.py`

**Features:**
- SSL certificate management
- Self-signed certificate generation (development)
- TLS 1.2+ enforcement
- Secure cipher suites
- HTTP to HTTPS redirect

**Development Setup:**
```python
from app.middleware.tls_config import configure_app_tls

ssl_context = configure_app_tls(
    app,
    cert_file='instance/ssl/cert.pem',
    key_file='instance/ssl/key.pem',
    generate_self_signed=True  # Auto-generate for dev
)

app.run(host='0.0.0.0', port=8443, ssl_context=ssl_context)
```

**Production Setup:**
```python
ssl_context = configure_app_tls(
    app,
    cert_file='/etc/ssl/certs/server.crt',  # Real certificate
    key_file='/etc/ssl/private/server.key',
    generate_self_signed=False
)
```

**Generate Certificate Manually:**
```python
from app.middleware.tls_config import TLSConfig

TLSConfig.generate_self_signed_cert(
    'cert.pem',
    'key.pem',
    domain='localhost'
)
```

### 6. ✅ Security Headers

**Location:** `app/middleware/security_headers.py`

**Features:**
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options (clickjacking prevention)
- X-Content-Type-Options (MIME sniffing prevention)
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
- CORS configuration

**Headers Applied:**
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; ...
Permissions-Policy: geolocation=(), microphone=(), ...
Server: GCP-Stimulator
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

**Setup:**
```python
from app.middleware.security_headers import configure_security

configure_security(
    app,
    enable_https=True,
    cors_origins=['http://localhost:3000', 'https://app.example.com']
)
```

### 7. ✅ Environment Configuration

**Location:** `app/config/security_config.py`

**Environments:**
- **Development**: No auth, no rate limiting, HTTP
- **Production**: Auth required, rate limiting, HTTPS
- **Testing**: Optional auth, no rate limiting

**Usage:**
```python
from app.config.security_config import SecurityConfig

config = SecurityConfig.get_config('production')
app.config.update(config)

# Print security status
SecurityConfig.print_security_status(config)
```

**Environment Variables:**
```bash
# Set environment
export FLASK_ENV=production

# Override specific settings
export AUTH_MODE=required
export RATE_LIMITING_ENABLED=true
export HTTPS_ENABLED=true
export JWT_SECRET_KEY=your-secret-key
export CORS_ORIGINS=https://app1.com,https://app2.com
```

---

## 📦 Installation & Setup

### 1. Install Dependencies

```bash
cd gcp-stimulator-package

# Install security-related packages
pip install PyJWT cryptography bleach redis
```

### 2. Run Database Migration

```bash
# Connect to PostgreSQL
docker exec -it gcs-emulator-db psql -U postgres -d gcs_emulator

# Run migration
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR(64) PRIMARY KEY,
    key_hash VARCHAR(128) NOT NULL UNIQUE,
    name VARCHAR(256),
    project_id VARCHAR(256) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    scopes VARCHAR(2048)
);

CREATE INDEX idx_api_keys_project ON api_keys(project_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);
```

Or use Python:
```python
from app.config.security_config import run_security_migrations
run_security_migrations(db.engine)
```

### 3. Update app/factory.py

Add to your application factory:

```python
from app.config.security_config import SecurityConfig
from app.middleware.auth_middleware import AuthConfig
from app.middleware.security_headers import configure_security
from app.middleware.tls_config import configure_app_tls
from app.routes.auth_routes import auth_mgmt_bp

def create_app(environment='development'):
    app = Flask(__name__)
    
    # Load security config
    config = SecurityConfig.get_config(environment)
    app.config.update(config)
    
    # Initialize authentication
    AuthConfig.initialize(app)
    
    # Register auth routes
    app.register_blueprint(auth_mgmt_bp)
    
    # Configure security headers and CORS
    configure_security(
        app,
        enable_https=app.config.get('HTTPS_ENABLED', False),
        cors_origins=app.config.get('CORS_ORIGINS', ['*'])
    )
    
    # Print security status
    SecurityConfig.print_security_status(app.config)
    
    return app
```

### 4. Start with Security

**Development:**
```bash
python run.py
# Runs on HTTP port 8080, no auth required
```

**Production:**
```bash
export FLASK_ENV=production
export AUTH_MODE=required
export HTTPS_ENABLED=true
export JWT_SECRET_KEY=$(openssl rand -hex 32)

python run.py
# Runs on HTTPS port 8443, auth required
```

---

## 🔐 Using Secured APIs

### Without Authentication (Development)

```bash
curl http://localhost:8080/storage/v1/b?project=my-project
```

### With API Key

```bash
# Generate API key
curl -X POST http://localhost:8080/auth/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-project",
    "name": "My API Key",
    "expires_days": 365
  }'

# Use API key
curl http://localhost:8080/storage/v1/b?project=my-project \
  -H "X-API-Key: gcps_abc123..."
```

### With JWT Token

```bash
# Generate token
curl -X POST http://localhost:8080/auth/tokens \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user@example.com",
    "project_id": "my-project"
  }'

# Use token
curl http://localhost:8080/storage/v1/b?project=my-project \
  -H "Authorization: Bearer eyJ..."
```

---

## ⚙️ Configuration Examples

### Example 1: Development (No Security)

```python
# config
AUTH_MODE = 'disabled'
RATE_LIMITING_ENABLED = False
HTTPS_ENABLED = False
CORS_ORIGINS = ['*']
```

### Example 2: Staging (Partial Security)

```python
# config
AUTH_MODE = 'optional'  # Track but don't enforce
RATE_LIMITING_ENABLED = True
HTTPS_ENABLED = True
CORS_ORIGINS = ['http://localhost:3000']
```

### Example 3: Production (Full Security)

```python
# config
AUTH_MODE = 'required'  # Enforce authentication
RATE_LIMITING_ENABLED = True
HTTPS_ENABLED = True
FORCE_HTTPS = True  # Redirect HTTP to HTTPS
CORS_ORIGINS = ['https://app.example.com']
```

---

## 🧪 Testing Security Features

### Test Authentication

```bash
# Should fail without auth (if AUTH_MODE=required)
curl http://localhost:8080/storage/v1/b?project=test

# Generate and use API key
KEY=$(curl -X POST http://localhost:8080/auth/api-keys -H "Content-Type: application/json" -d '{"project_id":"test","name":"Test"}' | jq -r '.api_key')

curl http://localhost:8080/storage/v1/b?project=test -H "X-API-Key: $KEY"
```

### Test Rate Limiting

```bash
# Make 100+ requests rapidly
for i in {1..110}; do
  curl http://localhost:8080/storage/v1/b?project=test -H "X-API-Key: $KEY"
done

# Should see 429 Rate Limit Exceeded after limit
```

### Test Input Validation

```bash
# Should fail - invalid project ID
curl -X POST http://localhost:8080/api/projects/INVALID_ID/buckets \
  -H "Content-Type: application/json" \
  -d '{"name":"test-bucket"}'

# Should succeed - valid input
curl -X POST http://localhost:8080/api/projects/my-project/buckets \
  -H "Content-Type: application/json" \
  -d '{"name":"test-bucket","location":"us-central1"}'
```

### Test HTTPS

```bash
# Generate self-signed cert
python -c "from app.middleware.tls_config import TLSConfig; TLSConfig.generate_self_signed_cert('cert.pem', 'key.pem')"

# Run with HTTPS
python run.py --https --cert cert.pem --key key.pem

# Test
curl -k https://localhost:8443/health
```

---

## 📊 Security Status Dashboard

Run this to see current security status:

```python
from app.config.security_config import SecurityConfig
import os

config = SecurityConfig.get_config(os.environ.get('FLASK_ENV', 'development'))
SecurityConfig.print_security_status(config)
```

Output:
```
============================================================
🔒 SECURITY CONFIGURATION STATUS
============================================================

📋 Authentication:
   Mode: REQUIRED
   Mock Auth: ❌ DISABLED
   JWT Expiration: 24 hours

⚡ Rate Limiting:
   Status: ✅ ENABLED
   Backend: Redis (redis://localhost:6379/0)

🔐 HTTPS/TLS:
   HTTPS: ✅ ENABLED
   Force HTTPS: ✅ YES
   Certificate: /etc/ssl/certs/server.crt

🌐 CORS:
   Allowed Origins: 2 configured
      - https://app.example.com
      - https://admin.example.com

🌍 Environment:
   Mode: PRODUCTION
   Debug: ❌ OFF
   Log Level: INFO

⚠️  Security Warnings:
   ✅ No security warnings

============================================================
```

---

## ✅ Phase 1 Complete!

All Phase 1 security features are implemented and ready to use. The system can now:

- ✅ Authenticate users with JWT or API keys
- ✅ Rate limit requests to prevent abuse
- ✅ Validate all inputs to prevent injection attacks
- ✅ Run over HTTPS with TLS
- ✅ Apply security headers to all responses
- ✅ Configure for different environments

**Next Steps:**
- Test all features in staging
- Configure for your production environment
- Set up monitoring and logging
- Proceed to Phase 2 (Deployment & Reliability)
