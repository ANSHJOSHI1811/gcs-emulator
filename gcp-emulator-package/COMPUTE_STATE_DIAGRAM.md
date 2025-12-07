# Compute Engine Instance State Diagram (Phase 2)

## Visual State Flow

```
                    ┌─────────────────────────────────────────┐
                    │           CREATE INSTANCE               │
                    │  POST /instances                        │
                    └──────────────┬──────────────────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │  PROVISIONING    │ ◄── Initial state
                        │  (transient)     │
                        └────────┬─────────┘
                                 │ (automatic)
                                 ▼
                        ┌──────────────────┐
                        │    STAGING       │ ◄── Preparing instance
                        │  (transient)     │
                        └────────┬─────────┘
                                 │ (automatic)
                                 ▼
                        ┌──────────────────┐
                        │    RUNNING       │ ◄── Instance active
                        │   (stable)       │
                        └────────┬─────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │ STOP                          │ DELETE (if RUNNING)
                 │ POST /stop                    │ DELETE /instances/{name}
                 ▼                               ▼
        ┌──────────────────┐          ┌──────────────────┐
        │    STOPPING      │          │    STOPPING      │
        │  (transient)     │          │  (transient)     │
        └────────┬─────────┘          └────────┬─────────┘
                 │ (automatic)                 │ (automatic)
                 ▼                             ▼
        ┌──────────────────┐          ┌──────────────────┐
        │   TERMINATED     │          │   TERMINATED     │
        │   (stable)       │          │   (transient)    │
        └────────┬─────────┘          └────────┬─────────┘
                 │                              │
                 │ START                        │ DELETE
                 │ POST /start                  │ (remove from DB)
                 │                              ▼
                 │                        [INSTANCE DELETED]
                 │
                 ▼
        ┌──────────────────┐
        │    STAGING       │
        │  (transient)     │
        └────────┬─────────┘
                 │ (automatic)
                 ▼
        ┌──────────────────┐
        │    RUNNING       │
        │   (stable)       │
        └──────────────────┘
```

---

## State Details

### Stable States (User-visible)
These are the states where an instance can remain:

| State | Description | Duration | User Actions |
|-------|-------------|----------|--------------|
| **RUNNING** | Instance is active and operational | Indefinite | Stop, Delete |
| **TERMINATED** | Instance is stopped | Indefinite | Start, Delete |

### Transient States (Automatic transitions)
These states are passed through automatically:

| State | Description | Duration | Next State |
|-------|-------------|----------|------------|
| **PROVISIONING** | Initial creation | Instant | STAGING |
| **STAGING** | Preparing to run | Instant | RUNNING |
| **STOPPING** | Shutting down | Instant | TERMINATED |

---

## Operation Matrix

| Current State | CREATE | START | STOP | DELETE |
|--------------|--------|-------|------|--------|
| (none) | ✅ RUNNING | N/A | N/A | N/A |
| PROVISIONING | ❌ | ❌ | ❌ | ✅ |
| STAGING | ❌ | ❌ | ❌ | ✅ |
| RUNNING | ❌ | ❌ | ✅ TERMINATED | ✅ |
| STOPPING | ❌ | ❌ | ❌ | ✅ |
| TERMINATED | ❌ | ✅ RUNNING | ❌ | ✅ |

Legend:
- ✅ = Operation allowed
- ❌ = Operation returns 400 error
- N/A = Not applicable

---

## HTTP Status Codes

### Success Cases
| Operation | Current State | HTTP Status | Final State |
|-----------|---------------|-------------|-------------|
| CREATE | (none) | 200 OK | RUNNING |
| START | TERMINATED | 200 OK | RUNNING |
| STOP | RUNNING | 200 OK | TERMINATED |
| DELETE | RUNNING | 200 OK | (deleted) |
| DELETE | TERMINATED | 200 OK | (deleted) |
| GET | any | 200 OK | (unchanged) |
| LIST | any | 200 OK | (unchanged) |

### Error Cases
| Operation | Current State | HTTP Status | Error Message |
|-----------|---------------|-------------|---------------|
| CREATE | RUNNING (duplicate) | 409 Conflict | "Instance already exists" |
| START | RUNNING | 400 Bad Request | "Cannot start instance in 'RUNNING' state" |
| START | PROVISIONING | 400 Bad Request | "Cannot start instance in 'PROVISIONING' state" |
| STOP | TERMINATED | 400 Bad Request | "Cannot stop instance in 'TERMINATED' state" |
| STOP | PROVISIONING | 400 Bad Request | "Cannot stop instance in 'PROVISIONING' state" |
| GET | (nonexistent) | 404 Not Found | "Instance not found" |
| START | (nonexistent) | 404 Not Found | "Instance not found" |
| STOP | (nonexistent) | 404 Not Found | "Instance not found" |
| DELETE | (nonexistent) | 404 Not Found | "Instance not found" |

---

## Transition Timings (Phase 2)

In Phase 2, all transitions are **synchronous and instant**:

| Transition | Duration | Implementation |
|------------|----------|----------------|
| PROVISIONING → STAGING | Instant | Synchronous DB update |
| STAGING → RUNNING | Instant | Synchronous DB update |
| RUNNING → STOPPING | Instant | Synchronous DB update |
| STOPPING → TERMINATED | Instant | Synchronous DB update |
| TERMINATED → STAGING | Instant | Synchronous DB update |

**Note**: In Phase 3 (with Docker), these will become asynchronous with actual provisioning time.

---

## Timestamp Updates

| Operation | Timestamp Updated | Value |
|-----------|------------------|-------|
| CREATE | `creation_timestamp` | Current UTC time |
| CREATE | `last_start_timestamp` | Current UTC time |
| START | `last_start_timestamp` | Current UTC time |
| STOP | `last_stop_timestamp` | Current UTC time |

---

## Example Flows

### Flow 1: Standard Lifecycle
```
1. CREATE instance "web-server"
   → PROVISIONING → STAGING → RUNNING
   
2. STOP instance "web-server"
   → RUNNING → STOPPING → TERMINATED
   
3. START instance "web-server"
   → TERMINATED → STAGING → RUNNING
   
4. DELETE instance "web-server"
   → RUNNING → STOPPING → TERMINATED → (removed)
```

### Flow 2: Immediate Delete
```
1. CREATE instance "temp-vm"
   → PROVISIONING → STAGING → RUNNING
   
2. DELETE instance "temp-vm" (while RUNNING)
   → RUNNING → STOPPING → TERMINATED → (removed)
```

### Flow 3: Error Case
```
1. CREATE instance "my-vm"
   → PROVISIONING → STAGING → RUNNING
   
2. START instance "my-vm" (already RUNNING)
   → ERROR 400: "Cannot start instance in 'RUNNING' state"
   → State remains: RUNNING
```

---

## Implementation Notes

### Phase 2 Behavior
- All state transitions happen in-process (synchronous)
- No background workers or queues
- Status updates are immediate
- No actual resources are provisioned

### Phase 3 Changes (Future)
- Docker container creation during PROVISIONING
- Actual startup time during STAGING
- Real shutdown during STOPPING
- Container lifecycle tied to instance state
- Asynchronous operations with polling

---

## Validation Rules

### Before START
```python
if instance.status != InstanceStatus.TERMINATED:
    raise InvalidStateError(
        f"Cannot start instance in '{instance.status}' state. "
        f"Instance must be in TERMINATED state."
    )
```

### Before STOP
```python
if instance.status != InstanceStatus.RUNNING:
    raise InvalidStateError(
        f"Cannot stop instance in '{instance.status}' state. "
        f"Instance must be in RUNNING state."
    )
```

### Before DELETE
```python
# No validation - DELETE is always allowed
# If RUNNING, will force stop first
if instance.status == InstanceStatus.RUNNING:
    # Transition: RUNNING → STOPPING → TERMINATED
    # Then delete from database
```

---

## References

- **Implementation**: `app/services/compute_service.py`
- **Tests**: `tests/test_compute_phase2.py`
- **State Enum**: `app/models/compute.py` - `InstanceStatus` class
- **Validation**: `InstanceStatus.can_transition()` method
