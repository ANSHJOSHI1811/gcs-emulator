# IAM Module Quick Start Guide

## Setup (5 minutes)

### 1. Run Migration

```bash
cd gcp-emulator-package
python migrations/005_add_iam_tables.py
```

### 2. Start Backend

```bash
python run.py
```

Backend will be available at `http://localhost:8080`

### 3. Start Frontend

```bash
cd ../gcp-emulator-ui
npm install  # if first time
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Quick Examples

### Using the UI

1. Navigate to `http://localhost:3000/services/iam`
2. Click "Create Service Account"
3. Fill in account details and submit
4. View service accounts in the table
5. Switch to "Roles" tab to see predefined and custom roles

### Using the REST API

#### Create a Service Account

```bash
curl -X POST http://localhost:8080/v1/projects/my-project/serviceAccounts \
  -H "Content-Type: application/json" \
  -d '{
    "accountId": "my-test-sa",
    "displayName": "My Test Service Account",
    "description": "Used for local testing"
  }'
```

#### List Service Accounts

```bash
curl http://localhost:8080/v1/projects/my-project/serviceAccounts
```

#### Create a Service Account Key

```bash
curl -X POST http://localhost:8080/v1/projects/my-project/serviceAccounts/my-test-sa@my-project.iam.gserviceaccount.com/keys \
  -H "Content-Type: application/json"
```

This returns credentials JSON in `privateKeyData` (base64 encoded).

#### Set IAM Policy on a Bucket

```bash
curl -X POST http://localhost:8080/v1/projects/my-project/buckets/my-bucket:setIamPolicy \
  -H "Content-Type: application/json" \
  -d '{
    "policy": {
      "version": 1,
      "bindings": [
        {
          "role": "roles/storage.objectViewer",
          "members": [
            "serviceAccount:my-test-sa@my-project.iam.gserviceaccount.com"
          ]
        }
      ]
    }
  }'
```

### Using the CLI

#### Service Accounts

```bash
# List
flask iam service-accounts list --project my-project

# Create
flask iam service-accounts create my-cli-sa \
  --project my-project \
  --display-name "CLI Test SA"

# Get details
flask iam service-accounts describe my-cli-sa@my-project.iam.gserviceaccount.com

# Delete
flask iam service-accounts delete my-cli-sa@my-project.iam.gserviceaccount.com
```

#### Keys

```bash
# Create key (saves to JSON file)
flask iam keys create my-cli-sa@my-project.iam.gserviceaccount.com

# List keys
flask iam keys list my-cli-sa@my-project.iam.gserviceaccount.com
```

#### Roles

```bash
# List all roles
flask iam roles list

# Create custom role
flask iam roles create myCustomRole \
  --project my-project \
  --title "My Custom Role" \
  --permissions "storage.objects.get,storage.objects.list"

# Describe role
flask iam roles describe roles/storage.objectViewer
```

## Testing with Python

```python
import requests
import base64
import json

BASE_URL = "http://localhost:8080"
PROJECT = "my-project"

# 1. Create service account
response = requests.post(
    f"{BASE_URL}/v1/projects/{PROJECT}/serviceAccounts",
    json={
        "accountId": "python-test-sa",
        "displayName": "Python Test SA"
    }
)
sa = response.json()
print(f"Created: {sa['email']}")

# 2. Create key
response = requests.post(
    f"{BASE_URL}/v1/projects/{PROJECT}/serviceAccounts/{sa['email']}/keys"
)
key = response.json()

# 3. Decode credentials
creds = json.loads(base64.b64decode(key['privateKeyData']))
print(f"Key ID: {creds['private_key_id']}")
print(f"Client Email: {creds['client_email']}")

# 4. Save credentials to file
with open('sa-credentials.json', 'w') as f:
    json.dump(creds, f, indent=2)

print("Credentials saved to sa-credentials.json")

# 5. Get IAM policy for a bucket
response = requests.post(
    f"{BASE_URL}/v1/projects/{PROJECT}/buckets/test-bucket:getIamPolicy"
)
policy = response.json()
print(f"Current bindings: {len(policy.get('bindings', []))}")

# 6. Add service account to bucket policy
policy['bindings'].append({
    "role": "roles/storage.objectAdmin",
    "members": [f"serviceAccount:{sa['email']}"]
})

response = requests.post(
    f"{BASE_URL}/v1/projects/{PROJECT}/buckets/test-bucket:setIamPolicy",
    json={"policy": policy}
)
print("Policy updated!")
```

## Common Use Cases

### 1. Local Development with Service Accounts

Create a service account and key for your local app:

```bash
# Create SA
curl -X POST http://localhost:8080/v1/projects/my-project/serviceAccounts \
  -H "Content-Type: application/json" \
  -d '{"accountId": "local-dev-sa"}' > sa.json

# Extract email
EMAIL=$(cat sa.json | jq -r .email)

# Create key
curl -X POST "http://localhost:8080/v1/projects/my-project/serviceAccounts/$EMAIL/keys" \
  | jq -r .privateKeyData | base64 -d > credentials.json

# Use in your app
export GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
```

### 2. Testing IAM Permissions

```bash
# Test what permissions a user/SA has
curl -X POST http://localhost:8080/v1/projects/my-project/buckets/my-bucket:testIamPermissions \
  -H "Content-Type: application/json" \
  -d '{
    "permissions": [
      "storage.objects.get",
      "storage.objects.list",
      "storage.objects.create",
      "storage.objects.delete"
    ]
  }'
```

### 3. Creating Custom Roles

```bash
# Create a read-only custom role
curl -X POST http://localhost:8080/v1/projects/my-project/roles \
  -H "Content-Type: application/json" \
  -d '{
    "roleId": "customReader",
    "title": "Custom Reader",
    "description": "Can only read objects",
    "includedPermissions": [
      "storage.objects.get",
      "storage.objects.list"
    ]
  }'
```

## Next Steps

- Read full documentation: [IAM_MODULE.md](IAM_MODULE.md)
- Explore the UI at `http://localhost:3000/services/iam`
- Test with your application by pointing it to `http://localhost:8080`
- Check out the API endpoints documentation

## Troubleshooting

### Migration fails
```bash
# Check database connection
psql $DATABASE_URL -c "SELECT 1"

# Try manual migration
python
>>> from app import create_app
>>> app = create_app()
>>> with app.app_context():
...     from migrations import upgrade
...     upgrade()
```

### UI not loading IAM data
- Check backend is running: `curl http://localhost:8080/v1/roles`
- Check browser console for errors
- Verify API_BASE_URL in frontend config

### CLI commands not working
```bash
# Ensure Flask app context
cd gcp-emulator-package
export FLASK_APP=run.py
flask iam --help
```

## Support

For issues or questions:
1. Check the full documentation
2. Review example code in the docs
3. Test endpoints with curl first
4. Check backend logs for errors
