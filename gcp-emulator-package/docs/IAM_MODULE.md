# IAM Module Documentation

## Overview

The IAM (Identity and Access Management) module provides a complete simulation of Google Cloud IAM functionality, allowing you to manage service accounts, roles, and policies locally. This is fully compatible with the `gcloud` CLI and can be used to test IAM-dependent applications.

## Features

### Service Accounts
- Create, list, update, and delete service accounts
- Enable/disable service accounts
- Generate service account keys with mock credentials
- Full email-based identification (`<account>@<project>.iam.gserviceaccount.com`)

### IAM Roles
- Predefined roles (storage.admin, storage.objectViewer, etc.)
- Custom role creation and management
- Role permissions management
- Soft delete and undelete for custom roles

### IAM Policies
- Get and set IAM policies on resources
- Role bindings with member management
- Support for multiple member types (user, serviceAccount, allUsers)
- ETag-based optimistic concurrency control

## Quick Start

### 1. Run Database Migration

```bash
cd gcp-emulator-package
python migrations/005_add_iam_tables.py
```

### 2. Start the Emulator

```bash
python run.py
```

The IAM endpoints are now available at `http://localhost:8080/v1/`

### 3. Using the UI

Navigate to `http://localhost:3000/services/iam` to access:
- Service Accounts management
- IAM Roles browser

## API Endpoints

### Service Accounts

#### Create Service Account
```http
POST /v1/projects/{project}/serviceAccounts
Content-Type: application/json

{
  "accountId": "my-service-account",
  "displayName": "My Service Account",
  "description": "Used for testing"
}
```

#### List Service Accounts
```http
GET /v1/projects/{project}/serviceAccounts
```

#### Get Service Account
```http
GET /v1/projects/{project}/serviceAccounts/{email}
```

#### Delete Service Account
```http
DELETE /v1/projects/{project}/serviceAccounts/{email}
```

#### Disable Service Account
```http
POST /v1/projects/{project}/serviceAccounts/{email}:disable
```

#### Enable Service Account
```http
POST /v1/projects/{project}/serviceAccounts/{email}:enable
```

### Service Account Keys

#### Create Key
```http
POST /v1/projects/{project}/serviceAccounts/{email}/keys
Content-Type: application/json

{
  "keyAlgorithm": "KEY_ALG_RSA_2048",
  "privateKeyType": "TYPE_GOOGLE_CREDENTIALS_FILE"
}
```

Response includes `privateKeyData` (base64-encoded JSON credentials).

#### List Keys
```http
GET /v1/projects/{project}/serviceAccounts/{email}/keys
```

#### Delete Key
```http
DELETE /v1/projects/{project}/serviceAccounts/{email}/keys/{keyId}
```

### IAM Policies

#### Get IAM Policy
```http
POST /v1/{resource}:getIamPolicy

# Examples:
POST /v1/projects/my-project:getIamPolicy
POST /v1/projects/my-project/buckets/my-bucket:getIamPolicy
```

#### Set IAM Policy
```http
POST /v1/{resource}:setIamPolicy
Content-Type: application/json

{
  "policy": {
    "version": 1,
    "bindings": [
      {
        "role": "roles/storage.objectViewer",
        "members": [
          "serviceAccount:my-sa@my-project.iam.gserviceaccount.com",
          "user:user@example.com"
        ]
      }
    ]
  }
}
```

#### Test IAM Permissions
```http
POST /v1/{resource}:testIamPermissions
Content-Type: application/json

{
  "permissions": [
    "storage.objects.get",
    "storage.objects.list"
  ]
}
```

### Roles

#### List Roles
```http
GET /v1/roles                           # List predefined roles
GET /v1/projects/{project}/roles        # List custom roles
```

#### Create Custom Role
```http
POST /v1/projects/{project}/roles
Content-Type: application/json

{
  "roleId": "customRole",
  "title": "Custom Role",
  "description": "My custom role",
  "includedPermissions": [
    "storage.objects.get",
    "storage.objects.list"
  ],
  "stage": "GA"
}
```

#### Get Role
```http
GET /v1/{roleName}

# Examples:
GET /v1/roles/storage.objectViewer
GET /v1/projects/my-project/roles/customRole
```

#### Delete Role
```http
DELETE /v1/{roleName}
```

## CLI Commands

### Service Accounts

```bash
# List service accounts
flask iam service-accounts list --project my-project

# Create service account
flask iam service-accounts create my-sa \
  --project my-project \
  --display-name "My Service Account" \
  --description "For testing"

# Describe service account
flask iam service-accounts describe my-sa@my-project.iam.gserviceaccount.com

# Disable service account
flask iam service-accounts disable my-sa@my-project.iam.gserviceaccount.com

# Enable service account
flask iam service-accounts enable my-sa@my-project.iam.gserviceaccount.com

# Delete service account
flask iam service-accounts delete my-sa@my-project.iam.gserviceaccount.com
```

### Service Account Keys

```bash
# List keys
flask iam keys list my-sa@my-project.iam.gserviceaccount.com

# Create key (saves to file)
flask iam keys create my-sa@my-project.iam.gserviceaccount.com

# Delete key
flask iam keys delete projects/my-project/serviceAccounts/my-sa@my-project.iam.gserviceaccount.com/keys/abc123
```

### Roles

```bash
# List all roles
flask iam roles list

# List custom roles only
flask iam roles list --project my-project

# Create custom role
flask iam roles create customRole \
  --project my-project \
  --title "Custom Role" \
  --description "My custom role" \
  --permissions "storage.objects.get,storage.objects.list"

# Describe role
flask iam roles describe roles/storage.objectViewer

# Delete role
flask iam roles delete projects/my-project/roles/customRole
```

## Using with gcloud CLI

Point gcloud to your local emulator:

```bash
# Set emulator host
export IAM_EMULATOR_HOST=http://localhost:8080

# Now use gcloud commands (some may need custom wrappers)
# Direct REST API calls work best:

curl -X POST http://localhost:8080/v1/projects/my-project/serviceAccounts \
  -H "Content-Type: application/json" \
  -d '{
    "accountId": "test-sa",
    "displayName": "Test Service Account"
  }'
```

## Python SDK Usage

```python
# Note: The Google Cloud IAM SDK expects specific authentication
# For testing, use direct REST API calls or create a custom client

import requests

BASE_URL = "http://localhost:8080"
PROJECT_ID = "my-project"

# Create service account
response = requests.post(
    f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts",
    json={
        "accountId": "my-test-sa",
        "displayName": "Test SA"
    }
)
service_account = response.json()
print(f"Created: {service_account['email']}")

# Create key
response = requests.post(
    f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts/{service_account['email']}/keys",
    json={"keyAlgorithm": "KEY_ALG_RSA_2048"}
)
key = response.json()

# Decode private key
import base64
import json
credentials = json.loads(base64.b64decode(key['privateKeyData']))
print(f"Private Key ID: {credentials['private_key_id']}")

# Set IAM policy on a bucket
response = requests.post(
    f"{BASE_URL}/v1/projects/{PROJECT_ID}/buckets/my-bucket:setIamPolicy",
    json={
        "policy": {
            "version": 1,
            "bindings": [
                {
                    "role": "roles/storage.objectViewer",
                    "members": [f"serviceAccount:{service_account['email']}"]
                }
            ]
        }
    }
)
policy = response.json()
print(f"Policy set with {len(policy['bindings'])} bindings")
```

## Predefined Roles

The emulator comes with several predefined GCS roles:

| Role Name | Title | Permissions |
|-----------|-------|-------------|
| `roles/storage.objectViewer` | Storage Object Viewer | `storage.objects.get`, `storage.objects.list` |
| `roles/storage.objectCreator` | Storage Object Creator | `storage.objects.create` |
| `roles/storage.objectAdmin` | Storage Object Admin | All object permissions |
| `roles/storage.admin` | Storage Admin | All storage permissions |
| `roles/owner` | Owner | All permissions (`*`) |
| `roles/editor` | Editor | All permissions (`*`) |
| `roles/viewer` | Viewer | Read permissions (`*.get`, `*.list`) |

## Architecture

### Backend Structure
```
app/
├── models/
│   ├── service_account.py     # ServiceAccount, ServiceAccountKey models
│   └── iam_policy.py          # IAMPolicy, IAMBinding, Role models
├── repositories/
│   └── iam_repository.py      # Data access layer
├── services/
│   └── iam_service.py         # Business logic layer
├── handlers/
│   └── iam_handler.py         # HTTP request handlers
├── serializers/
│   └── iam_serializers.py     # Request/response serialization
├── dtos/
│   └── iam_dtos.py           # Data transfer objects
└── cli/
    └── iam_commands.py        # CLI commands
```

### Database Schema

**service_accounts**
- `email` (PK): Service account email
- `project_id` (FK): Project reference
- `unique_id`: Numeric unique identifier
- `disabled`: Status flag

**service_account_keys**
- `id` (PK): Key resource name
- `service_account_email` (FK): Parent service account
- `private_key_data`: Base64-encoded credentials

**iam_policies**
- `resource_name`: Resource identifier (e.g., projects/x, buckets/y)
- `resource_type`: Resource type
- `etag`: Optimistic concurrency control

**iam_bindings**
- `policy_id` (FK): Parent policy
- `role`: Role name
- `members[]`: Array of member identifiers

**iam_roles**
- `name`: Role resource name
- `is_custom`: Custom vs predefined flag
- `included_permissions[]`: Array of permissions

## Testing

### Integration Test Example

```python
import requests
import pytest

BASE_URL = "http://localhost:8080"
PROJECT_ID = "test-project"

def test_service_account_lifecycle():
    # Create
    response = requests.post(
        f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts",
        json={"accountId": "test-sa"}
    )
    assert response.status_code == 201
    sa = response.json()
    email = sa['email']
    
    # Get
    response = requests.get(f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts/{email}")
    assert response.status_code == 200
    
    # Create key
    response = requests.post(f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts/{email}/keys")
    assert response.status_code == 201
    assert 'privateKeyData' in response.json()
    
    # Delete
    response = requests.delete(f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts/{email}")
    assert response.status_code == 204
```

## Troubleshooting

### Service account already exists
- Service account emails must be unique across the project
- Delete existing service account first or use a different account ID

### Permission denied
- Check IAM policy bindings on the resource
- Ensure service account is enabled
- Verify member format (e.g., `serviceAccount:email@project.iam.gserviceaccount.com`)

### ETag mismatch
- Policy was modified concurrently
- Fetch latest policy and retry with new ETag

### Key creation fails
- Ensure service account exists and is enabled
- Check database connectivity

## Future Enhancements

- [ ] IAM conditions support
- [ ] Organization-level policies
- [ ] Service account impersonation
- [ ] Audit logging for IAM changes
- [ ] Policy simulator
- [ ] Workload Identity Federation

## Contributing

To add new IAM features:

1. Update models in `app/models/`
2. Add repository methods in `app/repositories/iam_repository.py`
3. Implement service logic in `app/services/iam_service.py`
4. Create handlers in `app/handlers/iam_handler.py`
5. Add UI components in `gcp-emulator-ui/src/pages/`
6. Update API client in `gcp-emulator-ui/src/api/iam.ts`
7. Add CLI commands in `app/cli/iam_commands.py`
8. Update documentation

## License

Same as parent project.
