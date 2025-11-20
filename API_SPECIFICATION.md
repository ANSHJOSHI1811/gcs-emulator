# GCP Cloud Storage Emulator - API Specification

**Version:** 1.0  
**Date:** November 20, 2025  
**Status:** Based on Real GCP SDK Testing  

---

## 1. BASE URL

```
http://localhost:5000/storage/v1
```

---

## 2. AUTHENTICATION

### Current Implementation
- SDK will send credentials and obtain access token from Google
- Our emulator can **ignore token validation** (accept any token)
- Credentials are required but not validated against Google

### For Testing
- Can use real credentials (from GCP account)
- Can use dummy credentials (any valid JSON structure)
- Token exchange will happen (but we don't validate result)

---

## 3. API ENDPOINTS

### 3.1 List Buckets

**Endpoint:** `GET /storage/v1/b`

**Query Parameters:**
- `project` (required): GCP Project ID
- `maxResults` (optional): Max results to return (default: 1000)
- `pageToken` (optional): Token for pagination
- `projection` (optional): Response detail level
  - `noAcl`: Minimal response (default)
  - `full`: Complete details
- `prettyPrint` (optional): Format JSON response (default: false)

**Example Request:**
```
GET /storage/v1/b?project=gen-lang-client-0790195659&projection=noAcl&prettyPrint=false
```

**Response (Success - 200):**
```json
{
  "kind": "storage#buckets",
  "items": [
    {
      "kind": "storage#bucket",
      "id": "bucket-id-123",
      "name": "my-bucket",
      "projectNumber": "123456789",
      "metageneration": "1",
      "state": "ACTIVE",
      "etag": "CAE=",
      "location": "US",
      "locationConstraint": "us-central1",
      "storageClass": "STANDARD",
      "rpo": "DEFAULT",
      "timeCreated": "2024-01-01T12:00:00.000Z",
      "updated": "2024-01-01T12:00:00.000Z",
      "versioning": {
        "enabled": false
      },
      "lifecycle": {
        "rule": []
      },
      "retentionPolicy": null,
      "labels": {},
      "website": null,
      "cors": [],
      "defaultEventBasedHold": false,
      "iamConfiguration": {
        "bucketPolicyOnly": {
          "enabled": false,
          "lockedTime": null
        },
        "publicAccessPrevention": "inherited",
        "uniformBucketLevelAccess": {
          "enabled": false,
          "lockedTime": null
        }
      },
      "encryption": null,
      "billing": null,
      "logging": null,
      "owner": null,
      "acl": null
    }
  ],
  "nextPageToken": null
}
```

**Response (No Buckets):**
```json
{
  "kind": "storage#buckets"
}
```

**Response (Error - 403 Forbidden):**
```json
{
  "error": {
    "code": 403,
    "message": "Permission denied. Insufficient permissions to access bucket.",
    "errors": [
      {
        "domain": "global",
        "reason": "forbidden",
        "message": "Permission denied. Insufficient permissions to access bucket."
      }
    ]
  }
}
```

---

### 3.2 Create Bucket

**Endpoint:** `POST /storage/v1/b`

**Query Parameters:**
- `project` (required): GCP Project ID

**Request Body:**
```json
{
  "name": "my-bucket",
  "location": "US",
  "storageClass": "STANDARD",
  "versioning": {
    "enabled": false
  },
  "lifecycle": {
    "rule": []
  },
  "cors": [],
  "labels": {},
  "logging": null,
  "acl": []
}
```

**Response (Success - 200):**
```json
{
  "kind": "storage#bucket",
  "id": "my-bucket",
  "name": "my-bucket",
  "projectNumber": "123456789",
  "metageneration": "1",
  "etag": "CAE=",
  "location": "US",
  "storageClass": "STANDARD",
  "timeCreated": "2024-11-20T15:30:00.000Z",
  "updated": "2024-11-20T15:30:00.000Z",
  "versioning": {
    "enabled": false
  }
}
```

**Response (Error - 409 Conflict):**
```json
{
  "error": {
    "code": 409,
    "message": "The bucket name is already taken.",
    "errors": [
      {
        "domain": "global",
        "reason": "conflict",
        "message": "The bucket name is already taken."
      }
    ]
  }
}
```

---

### 3.3 Get Bucket

**Endpoint:** `GET /storage/v1/b/{bucket}`

**Query Parameters:**
- `projection` (optional): Response detail level (noAcl, full)

**Example Request:**
```
GET /storage/v1/b/my-bucket?projection=full
```

**Response (Success - 200):**
```json
{
  "kind": "storage#bucket",
  "id": "my-bucket",
  "name": "my-bucket",
  "projectNumber": "123456789",
  "metageneration": "1",
  "etag": "CAE=",
  "location": "US",
  "storageClass": "STANDARD",
  "timeCreated": "2024-01-01T12:00:00.000Z",
  "updated": "2024-01-01T12:00:00.000Z",
  "versioning": {
    "enabled": false
  }
}
```

**Response (Error - 404 Not Found):**
```json
{
  "error": {
    "code": 404,
    "message": "The specified bucket does not exist.",
    "errors": [
      {
        "domain": "global",
        "reason": "notFound",
        "message": "The specified bucket does not exist."
      }
    ]
  }
}
```

---

### 3.4 Delete Bucket

**Endpoint:** `DELETE /storage/v1/b/{bucket}`

**Example Request:**
```
DELETE /storage/v1/b/my-bucket
```

**Response (Success - 204 No Content):**
```
(empty response)
```

**Response (Error - 404 Not Found):**
```json
{
  "error": {
    "code": 404,
    "message": "The specified bucket does not exist.",
    "errors": [
      {
        "domain": "global",
        "reason": "notFound",
        "message": "The specified bucket does not exist."
      }
    ]
  }
}
```

---

### 3.5 List Objects

**Endpoint:** `GET /storage/v1/b/{bucket}/o`

**Query Parameters:**
- `maxResults` (optional): Max results to return
- `pageToken` (optional): Token for pagination
- `prefix` (optional): Filter by prefix
- `delimiter` (optional): Delimiter for hierarchy
- `projection` (optional): Response detail level (noAcl, full)
- `versions` (optional): Include multiple versions
- `prettyPrint` (optional): Format JSON

**Example Request:**
```
GET /storage/v1/b/my-bucket/o?maxResults=1000&projection=full
```

**Response (Success - 200):**
```json
{
  "kind": "storage#objects",
  "items": [
    {
      "kind": "storage#object",
      "id": "my-bucket/file.txt/1234567890",
      "name": "file.txt",
      "bucket": "my-bucket",
      "generation": "1234567890",
      "metageneration": "1",
      "contentType": "text/plain",
      "timeCreated": "2024-11-20T15:30:00.000Z",
      "updated": "2024-11-20T15:30:00.000Z",
      "storageClass": "STANDARD",
      "timeStorageClassUpdated": "2024-11-20T15:30:00.000Z",
      "size": "1024",
      "md5Hash": "rL0Y20zC+Fzt72VPzMSk2A==",
      "crc32c": "AAAAAA==",
      "mediaLink": "https://www.googleapis.com/download/storage/v1/b/my-bucket/o/file.txt?generation=1234567890&alt=media",
      "contentEncoding": null,
      "contentLanguage": null,
      "cacheControl": null,
      "contentDisposition": null,
      "customTime": null,
      "metadata": {},
      "acl": null
    }
  ],
  "nextPageToken": null,
  "prefixes": []
}
```

**Response (No Objects):**
```json
{
  "kind": "storage#objects"
}
```

---

### 3.6 Upload Object

**Endpoint:** `POST /storage/v1/b/{bucket}/o`

**Query Parameters:**
- `uploadType` (optional): media, multipart, resumable
- `name` (required): Object name

**Request Headers:**
- `Content-Type`: MIME type of object
- `Content-MD5`: Base64 encoded MD5 hash (optional)
- `Cache-Control`: Cache control header (optional)
- `Content-Encoding`: Encoding (optional)

**Example Request:**
```
POST /storage/v1/b/my-bucket/o?uploadType=media&name=file.txt
Content-Type: text/plain
Content-MD5: rL0Y20zC+Fzt72VPzMSk2A==

[file content here]
```

**Response (Success - 200):**
```json
{
  "kind": "storage#object",
  "id": "my-bucket/file.txt/1234567890",
  "name": "file.txt",
  "bucket": "my-bucket",
  "generation": "1234567890",
  "metageneration": "1",
  "contentType": "text/plain",
  "timeCreated": "2024-11-20T15:30:00.000Z",
  "updated": "2024-11-20T15:30:00.000Z",
  "storageClass": "STANDARD",
  "timeStorageClassUpdated": "2024-11-20T15:30:00.000Z",
  "size": "1024",
  "md5Hash": "rL0Y20zC+Fzt72VPzMSk2A==",
  "crc32c": "AAAAAA=="
}
```

---

### 3.7 Download Object

**Endpoint:** `GET /storage/v1/b/{bucket}/o/{object}?alt=media`

**Example Request:**
```
GET /storage/v1/b/my-bucket/o/file.txt?alt=media
```

**Response (Success - 200):**
```
[binary file content]
```

**Response (Error - 404 Not Found):**
```json
{
  "error": {
    "code": 404,
    "message": "The specified object does not exist.",
    "errors": [
      {
        "domain": "global",
        "reason": "notFound",
        "message": "The specified object does not exist."
      }
    ]
  }
}
```

---

### 3.8 Delete Object

**Endpoint:** `DELETE /storage/v1/b/{bucket}/o/{object}`

**Example Request:**
```
DELETE /storage/v1/b/my-bucket/o/file.txt
```

**Response (Success - 204 No Content):**
```
(empty response)
```

---

### 3.9 Get Object Metadata

**Endpoint:** `GET /storage/v1/b/{bucket}/o/{object}`

**Query Parameters:**
- `projection` (optional): Response detail level

**Response (Success - 200):**
```json
{
  "kind": "storage#object",
  "id": "my-bucket/file.txt/1234567890",
  "name": "file.txt",
  "bucket": "my-bucket",
  "generation": "1234567890",
  "metageneration": "1",
  "contentType": "text/plain",
  "timeCreated": "2024-11-20T15:30:00.000Z",
  "updated": "2024-11-20T15:30:00.000Z",
  "storageClass": "STANDARD",
  "size": "1024",
  "md5Hash": "rL0Y20zC+Fzt72VPzMSk2A==",
  "crc32c": "AAAAAA=="
}
```

---

## 4. RESPONSE FIELD DEFINITIONS

### Bucket Fields

| Field | Type | Description |
|-------|------|-------------|
| kind | string | "storage#bucket" |
| id | string | Bucket name (same as name field) |
| name | string | Bucket name |
| projectNumber | string | GCP project number |
| metageneration | string | Metadata generation counter |
| etag | string | Entity tag |
| location | string | Bucket location (US, EU, ASIA, etc.) |
| locationConstraint | string | Constraint location |
| storageClass | string | Storage class (STANDARD, NEARLINE, etc.) |
| rpo | string | Recovery Point Objective |
| timeCreated | string | Creation timestamp (ISO8601 UTC) |
| updated | string | Last update timestamp (ISO8601 UTC) |
| versioning | object | Versioning configuration |
| lifecycle | object | Lifecycle rules |
| retentionPolicy | object | Retention policy (nullable) |
| labels | object | User labels (key-value pairs) |
| website | object | Website config (nullable) |
| cors | array | CORS configuration |
| defaultEventBasedHold | boolean | Event-based hold flag |
| iamConfiguration | object | IAM configuration |
| encryption | object | Encryption config (nullable) |
| billing | object | Billing config (nullable) |
| logging | object | Logging config (nullable) |
| owner | object | Owner info (nullable) |
| acl | array | ACL (nullable) |

### Object Fields

| Field | Type | Description |
|-------|------|-------------|
| kind | string | "storage#object" |
| id | string | Unique object ID (bucket/name/generation) |
| name | string | Object name |
| bucket | string | Bucket name |
| generation | string | Object generation (version ID) |
| metageneration | string | Metadata generation counter |
| contentType | string | MIME type |
| timeCreated | string | Creation timestamp (ISO8601 UTC) |
| updated | string | Last update timestamp (ISO8601 UTC) |
| storageClass | string | Storage class |
| timeStorageClassUpdated | string | When storage class changed |
| size | string | Object size in bytes (as string!) |
| md5Hash | string | Base64-encoded MD5 hash |
| crc32c | string | Base64-encoded CRC32C hash |
| mediaLink | string | Download URL |
| contentEncoding | string | Content encoding (nullable) |
| contentLanguage | string | Content language (nullable) |
| cacheControl | string | Cache control header (nullable) |
| contentDisposition | string | Content disposition (nullable) |
| customTime | string | Custom timestamp (nullable) |
| metadata | object | Custom user metadata |
| acl | array | ACL (nullable) |

---

## 5. ERROR HANDLING

### Error Response Format
```json
{
  "error": {
    "code": 404,
    "message": "The specified bucket does not exist.",
    "errors": [
      {
        "domain": "global",
        "reason": "notFound",
        "message": "The specified bucket does not exist."
      }
    ]
  }
}
```

### HTTP Status Codes

| Code | Status | Reason | Example |
|------|--------|--------|---------|
| 200 | OK | Success | Bucket created, object uploaded |
| 204 | No Content | Success (no body) | Delete bucket, delete object |
| 400 | Bad Request | Invalid input | Malformed bucket name |
| 401 | Unauthorized | Auth failed | Invalid credentials |
| 403 | Forbidden | No permission | Permission denied |
| 404 | Not Found | Resource missing | Bucket doesn't exist |
| 409 | Conflict | Already exists | Bucket name taken |
| 412 | Precondition Failed | Condition failed | ETag mismatch |
| 500 | Server Error | Internal error | Unexpected error |

### Error Reasons

| Reason | HTTP Code | Description |
|--------|-----------|-------------|
| notFound | 404 | Resource doesn't exist |
| conflict | 409 | Resource already exists |
| forbidden | 403 | Permission denied |
| badRequest | 400 | Invalid input |
| unauthorized | 401 | Authentication failed |
| internal | 500 | Server error |

---

## 6. TIMESTAMP FORMAT

All timestamps must be in **ISO8601 format with UTC timezone**:

```
2024-11-20T15:30:00.000Z
```

Format: `YYYY-MM-DDTHH:MM:SS.fffZ`
- Always include milliseconds
- Always use Z (UTC timezone indicator)
- Never use +00:00 or other timezone indicators

---

## 7. NUMERIC FIELDS AS STRINGS

**Important:** Some numeric fields are returned as strings:
- `size`: "1024" (not 1024)
- `generation`: "1234567890" (not 1234567890)
- `metageneration`: "1" (not 1)
- `code`: 404 (as number in error)

This is intentional to preserve precision in JSON.

---

## 8. IMPLEMENTATION CHECKLIST

### MVP Phase 1
- [ ] List Buckets (GET /storage/v1/b)
- [ ] Create Bucket (POST /storage/v1/b)
- [ ] Get Bucket (GET /storage/v1/b/{bucket})
- [ ] Delete Bucket (DELETE /storage/v1/b/{bucket})

### MVP Phase 2
- [ ] List Objects (GET /storage/v1/b/{bucket}/o)
- [ ] Upload Object (POST /storage/v1/b/{bucket}/o)
- [ ] Get Object Metadata (GET /storage/v1/b/{bucket}/o/{object})
- [ ] Download Object (GET /storage/v1/b/{bucket}/o/{object}?alt=media)
- [ ] Delete Object (DELETE /storage/v1/b/{bucket}/o/{object})

### Future Phase 3
- [ ] Multipart Upload
- [ ] Object Versioning
- [ ] Signed URLs
- [ ] Access Control (IAM)
- [ ] Lifecycle Rules

---

## 9. TESTING CONFIGURATION

### Test Client Setup
```python
from google.oauth2 import service_account
from google.cloud import storage

# Load credentials
creds = service_account.Credentials.from_service_account_file('credentials.json')

# Create client
client = storage.Client(credentials=creds, project='test-project')

# Point to emulator
client._api_endpoint = 'http://localhost:5000'

# Now all calls go to emulator
buckets = list(client.list_buckets())
```

### Dummy Credentials Template
See `GCP_SDK_FINDINGS.md` for dummy credentials JSON template.

---

## 10. VALIDATION RULES

### Bucket Name
- 3-63 characters
- Lowercase letters, numbers, hyphens only
- Must start with letter or number
- No consecutive hyphens
- Must be globally unique

### Object Name
- Max 1024 characters
- Can contain any UTF-8 character
- No leading/trailing spaces
- Reserved: `.` and `..`

---

