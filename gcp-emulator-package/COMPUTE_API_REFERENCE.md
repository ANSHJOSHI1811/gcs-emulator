# Compute Engine API Quick Reference (Phase 2)

## Base URL
```
http://localhost:8080/compute
```

## Authentication
None (emulator mode)

---

## Endpoints

### 1. CREATE INSTANCE
**Creates a new instance (ends in RUNNING state)**

```http
POST /v1/projects/{project}/zones/{zone}/instances
Content-Type: application/json

{
  "name": "my-instance",
  "machineType": "zones/us-central1-a/machineTypes/e2-medium",
  "metadata": {
    "items": [{"key": "startup-script", "value": "echo hello"}]
  },
  "labels": {"env": "dev"},
  "tags": {"items": ["http-server"]}
}
```

**Response:** `200 OK` with `compute#operation`

**Errors:**
- `409` - Instance already exists
- `400` - Invalid machine type or parameters
- `404` - Project not found

---

### 2. LIST INSTANCES
**Lists all instances in a zone**

```http
GET /v1/projects/{project}/zones/{zone}/instances
```

**Response:** `200 OK` with `compute#instanceList`

---

### 3. GET INSTANCE
**Gets details of a specific instance**

```http
GET /v1/projects/{project}/zones/{zone}/instances/{name}
```

**Response:** `200 OK` with `compute#instance`

**Errors:**
- `404` - Instance not found

---

### 4. START INSTANCE
**Starts a TERMINATED instance**

```http
POST /v1/projects/{project}/zones/{zone}/instances/{name}/start
```

**Precondition:** Instance must be in `TERMINATED` state

**Response:** `200 OK` with `compute#operation`

**Errors:**
- `400` - Instance not in TERMINATED state
- `404` - Instance not found

**State Transition:** `TERMINATED → STAGING → RUNNING`

---

### 5. STOP INSTANCE
**Stops a RUNNING instance**

```http
POST /v1/projects/{project}/zones/{zone}/instances/{name}/stop
```

**Precondition:** Instance must be in `RUNNING` state

**Response:** `200 OK` with `compute#operation`

**Errors:**
- `400` - Instance not in RUNNING state
- `404` - Instance not found

**State Transition:** `RUNNING → STOPPING → TERMINATED`

---

### 6. DELETE INSTANCE
**Deletes an instance (force stops if RUNNING)**

```http
DELETE /v1/projects/{project}/zones/{zone}/instances/{name}
```

**Behavior:**
- If RUNNING: Force stop → delete
- If TERMINATED: Delete directly

**Response:** `200 OK` with `compute#operation`

**Errors:**
- `404` - Instance not found

---

## Machine Types

### List Machine Types
```http
GET /v1/projects/{project}/zones/{zone}/machineTypes
```

### Get Machine Type
```http
GET /v1/projects/{project}/zones/{zone}/machineTypes/{type}
```

### Available Types
- E2 Series: `e2-micro`, `e2-small`, `e2-medium`, `e2-standard-2/4/8`
- N1 Series: `n1-standard-1/2/4/8`
- N2 Series: `n2-standard-2/4/8`

---

## Instance States

| State | Description |
|-------|-------------|
| `PROVISIONING` | Initial creation (transient) |
| `STAGING` | Preparing instance (transient) |
| `RUNNING` | Instance is active |
| `STOPPING` | Shutting down (transient) |
| `TERMINATED` | Instance is stopped |

---

## Examples

### Example 1: Full Lifecycle
```bash
# 1. Create instance
curl -X POST http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances \
  -H "Content-Type: application/json" \
  -d '{"name": "test-vm", "machineType": "e2-medium"}'

# 2. List instances
curl http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances

# 3. Stop instance
curl -X POST http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances/test-vm/stop

# 4. Start instance
curl -X POST http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances/test-vm/start

# 5. Delete instance
curl -X DELETE http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances/test-vm
```

### Example 2: Error Handling
```bash
# Try to start an already running instance
curl -X POST http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances/test-vm/start

# Response: 400 Bad Request
{
  "error": {
    "code": 400,
    "message": "Cannot start instance in 'RUNNING' state. Instance must be in TERMINATED state."
  }
}
```

### Example 3: With Metadata
```bash
curl -X POST http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-server",
    "machineType": "zones/us-central1-a/machineTypes/e2-standard-2",
    "metadata": {
      "items": [
        {"key": "startup-script", "value": "#!/bin/bash\napt-get update\napt-get install -y nginx"},
        {"key": "environment", "value": "production"}
      ]
    },
    "labels": {
      "app": "web",
      "tier": "frontend",
      "env": "prod"
    },
    "tags": {
      "items": ["http-server", "https-server"]
    }
  }'
```

---

## Health Check

```http
GET /compute/health
```

**Response:**
```json
{
  "service": "compute-engine",
  "status": "healthy",
  "phase": "2 - Full REST API lifecycle"
}
```

---

## Common Error Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful operation |
| 400 | Bad Request | Invalid parameters or state |
| 404 | Not Found | Instance/project not found |
| 409 | Conflict | Duplicate instance name |
| 500 | Internal Error | Unexpected server error |

---

## Notes

- All timestamps are in ISO 8601 format with 'Z' suffix
- Machine types can be specified as full path or just name
- Zone format: `{region}-{zone}` (e.g., `us-central1-a`)
- Instance names: 1-63 lowercase alphanumeric + hyphens
- Phase 2 is metadata-only (no Docker containers yet)
