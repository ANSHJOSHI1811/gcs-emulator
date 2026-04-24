# DEVELOPMENT_RULES.md

**GCS Emulator Development Workflow & Standards**

> **Enforced Since**: April 24, 2026  
> **Strictness Level**: HIGH - Must follow all rules before committing  

---

## 🎯 Rule #1: Service Implementation Order (MANDATORY)

When implementing a new GCP service, you MUST follow this sequence:

### Phase 1️⃣: gcloud CLI Emulation (FIRST)
```
Start here → Implement gcloud commands in:
  tests/CloudTester/wrappers/{service_name}.py

Requirements:
  ✅ Each gcloud command has a Python wrapper function
  ✅ Wrapper returns same output as real gcloud (JSON/text match)
  ✅ Error handling matches GCP error messages
  ✅ All common operations covered (create, list, delete, update, describe)
  
Example (for compute service):
  gcloud compute instances create
  gcloud compute instances list
  gcloud compute instances delete
  gcloud compute instances describe
  
Success Criteria:
  - Run: pytest suites/gcloud_wrappers/test_{service}.py -v
  - Coverage: ≥ 80% of gcloud commands for that service
```

### Phase 2️⃣: Backend API Implementation (SECOND)
```
After gcloud → Implement FastAPI routes in:
  minimal-backend/api/{service_name}.py
  minimal-backend/services/{service_name}/

Structure:
  api/{service_name}.py
    - Route handlers (1 per endpoint)
    - Input validation with Pydantic
    - Error handling
    - Response formatting

  services/{service_name}/
    - Business logic (isolated from routes)
    - Database operations (SQLAlchemy)
    - Docker operations (if VM-related)
    - State synchronization

Requirements:
  ✅ All endpoints have request/response schemas
  ✅ Error codes match gcloud CLI errors
  ✅ Database models created in database.py
  ✅ Docker integration (if applicable)
  ✅ Endpoints match gcloud command structure

Success Criteria:
  - Run: pytest suites/{service}/test_api.py -v
  - Coverage: ≥ 85% of API endpoints
  - Endpoints respond with same data as gcloud wrappers
```

### Phase 3️⃣: Frontend Implementation (THIRD)
```
After API → Create React components in:
  gcp-stimulator-ui/src/pages/{ServiceName}.tsx
  gcp-stimulator-ui/src/api/{service_name}.ts

Structure:
  api/{service_name}.ts
    - Axios API client functions
    - Request/response types (TypeScript)
    - Error handling

  pages/{ServiceName}.tsx
    - Page component (React)
    - CRUD UI components
    - State management (Context/Hooks)
    - Real-time updates

  types/
    - TypeScript interfaces for {Service}

Requirements:
  ✅ All API endpoints have corresponding UI forms
  ✅ Real-time updates from backend
  ✅ Error messages displayed to user
  ✅ Responsive design (mobile & desktop)
  ✅ TypeScript types for all data

Success Criteria:
  - Manual testing: Create/List/Update/Delete operations work
  - No console errors
  - UI matches design system (Tailwind CSS)
```

### Phase 4️⃣: Complete Testing (FOURTH)
```
After all 3 → Run complete test suite:
  tests/CloudTester/suites/{service}/

Test Structure:
  test_gcloud_cli.py
    - gcloud command wrappers
    - Output format matching
    - Error message validation
    
  test_api.py
    - API endpoint functionality
    - Request validation
    - Database state
    - Docker container state
    
  test_integration.py
    - End-to-end workflows
    - gcloud → API → Frontend synchronization
    - State consistency

Requirements:
  ✅ gcloud tests: ≥ 90% command coverage
  ✅ API tests: ≥ 85% endpoint coverage
  ✅ Integration tests: ≥ 5 complete workflows
  ✅ Docker tests (if VM-related): ≥ 80% coverage
  ✅ All tests pass (0 failures)

Success Criteria:
  - Run: pytest suites/{service}/ -v --cov
  - Overall coverage: ≥ 85%
  - All tests pass
  - No flaky tests (runs consistently)
```

### Phase 5️⃣: Commit Only After All Phases Complete
```
Before committing:
  ✅ Phase 1: gcloud wrappers complete + tests pass
  ✅ Phase 2: API implementation complete + tests pass
  ✅ Phase 3: Frontend implementation complete
  ✅ Phase 4: All tests pass (gcloud + API + integration)
  ✅ Documentation updated (README, CLAUDE.md)
  ✅ No console errors or warnings
  ✅ Code linting passes

Commit Message Format:
  feat: implement {service} emulation
  
  - gcloud CLI: {command count} commands wrapped
  - API: {endpoint count} endpoints implemented
  - Frontend: CRUD UI pages created
  - Tests: {test count} tests, {coverage}% coverage
  - Docker: {status - if applicable}
  
  Closes: #{issue_number}
```

---

## 📋 Rule #2: Code Structure & Organization

### File Naming Conventions

#### Functions (ALPHABETICAL ORDER)
```python
# ✅ CORRECT - Alphabetical order
def create_bucket():
    pass

def delete_bucket():
    pass

def get_bucket():
    pass

def list_buckets():
    pass

def update_bucket():
    pass


# ❌ WRONG - Random order
def delete_bucket():
    pass

def create_bucket():
    pass

def list_buckets():
    pass
```

**Rule**: All functions in a file must be sorted alphabetically by name.

#### Classes
```python
# ✅ CORRECT
class StorageService:
    def create_bucket(self):
        pass
    
    def delete_bucket(self):
        pass
    
    def list_buckets(self):
        pass

# Methods inside classes also alphabetically ordered
```

#### Variables & Constants
```python
# ✅ CORRECT - UPPERCASE for constants, lowercase for variables
DATABASE_URL = "postgresql://..."
MAX_INSTANCES = 100
DEFAULT_ZONE = "us-central1-a"

instance_name = "my-instance"
network_cidr = "10.0.0.0/16"

# ❌ WRONG - Mixed case for constants
databaseUrl = "..."
maxInstances = 100
```

#### Files
```
✅ CORRECT naming:
  minimal-backend/
    ├── api/
    │   ├── autoscaling.py      (service name, lowercase)
    │   ├── compute.py
    │   ├── firewall.py
    │   ├── gke.py
    │   ├── iam.py
    │   ├── monitoring.py
    │   ├── routes.py
    │   ├── storage.py
    │   └── vpc.py
    │
    ├── services/
    │   ├── autoscaling/         (service name, lowercase, directory)
    │   ├── compute/
    │   ├── storage/
    │   └── vpc/
    │
    └── tests/
        └── CloudTester/
            └── suites/
                ├── autoscaling/
                ├── compute/
                ├── storage/
                └── vpc/
```

### Directory Structure Rules

```
Every new service MUST have:

minimal-backend/
  ├── api/
  │   └── {service_name}.py          # ← API routes
  │
  ├── services/
  │   └── {service_name}/
  │       ├── __init__.py
  │       ├── models.py              # Domain models
  │       └── operations.py           # Business logic
  │
  └── database.py                    # ← SQLAlchemy models

gcp-stimulator-ui/
  ├── src/
  │   ├── api/
  │   │   └── {service_name}.ts      # ← API client
  │   ├── pages/
  │   │   └── {ServiceName}.tsx      # ← UI page (PascalCase)
  │   └── types/
  │       └── {service_name}.ts      # ← TypeScript types

tests/
  └── CloudTester/
      ├── suites/
      │   └── {service_name}/
      │       ├── __init__.py
      │       ├── test_api.py         # ← API tests
      │       ├── test_gcloud_cli.py  # ← gcloud wrapper tests
      │       └── test_integration.py # ← End-to-end tests
      │
      └── wrappers/
          └── {service_name}.py       # ← gcloud CLI wrappers
```

---

## 🧪 Rule #3: Testing Requirements (MANDATORY)

### Test Coverage Thresholds

| Test Type | Minimum Coverage | File Location |
|-----------|-----------------|-----------------|
| gcloud CLI Wrappers | ≥ 80% | `tests/CloudTester/wrappers/{service}.py` |
| API Endpoints | ≥ 85% | `tests/CloudTester/suites/{service}/test_api.py` |
| Integration Tests | ≥ 75% | `tests/CloudTester/suites/{service}/test_integration.py` |
| **Overall** | **≥ 85%** | Coverage report |

### Test Execution Checklist

```bash
# Before committing ANY code, run this:

# 1️⃣ Run gcloud CLI wrapper tests first
pytest tests/CloudTester/suites/{service}/test_gcloud_cli.py -v

# 2️⃣ Run API tests
pytest tests/CloudTester/suites/{service}/test_api.py -v

# 3️⃣ Run integration tests
pytest tests/CloudTester/suites/{service}/test_integration.py -v

# 4️⃣ Run full service test suite
pytest tests/CloudTester/suites/{service}/ -v --cov

# 5️⃣ Check coverage report
coverage report -m

# All must pass before commit!
```

### What to Test

#### gcloud CLI Tests
```python
# tests/CloudTester/suites/{service}/test_gcloud_cli.py

def test_gcloud_create_{resource}():
    """Test: gcloud {service} {resource} create"""
    # Verify command executes
    # Verify output format (JSON/text)
    # Verify error handling
    pass

def test_gcloud_delete_{resource}():
    """Test: gcloud {service} {resource} delete"""
    pass

def test_gcloud_list_{resource}():
    """Test: gcloud {service} {resource} list"""
    pass

def test_gcloud_describe_{resource}():
    """Test: gcloud {service} {resource} describe"""
    pass
```

#### API Tests
```python
# tests/CloudTester/suites/{service}/test_api.py

def test_create_{resource}_api():
    """Test: POST /api/v1/{service}/{resource}"""
    # Valid request → 201
    # Invalid request → 400
    # Duplicate → 409
    pass

def test_list_{resource}_api():
    """Test: GET /api/v1/{service}/{resource}"""
    # List returns array
    # Filtering works
    # Pagination works
    pass

def test_delete_{resource}_api():
    """Test: DELETE /api/v1/{service}/{resource}/{id}"""
    # Existing resource → 204
    # Non-existent → 404
    # In-use resource → 409
    pass

def test_{resource}_state_sync_with_database():
    """Test: State persists in database after API call"""
    # Create via API
    # Query database
    # Verify state matches
    pass

def test_{resource}_state_sync_with_docker():
    """Test: Docker container state matches DB (if VM-related)"""
    # Create instance via API
    # Check Docker container
    # Verify state synchronization
    pass
```

#### Integration Tests
```python
# tests/CloudTester/suites/{service}/test_integration.py

def test_workflow_create_list_delete():
    """Complete workflow: Create → List → Delete"""
    # via gcloud CLI
    # Verify via API
    # Verify via Frontend (if applicable)
    pass

def test_state_consistency_gcloud_api_database():
    """State consistency across all layers"""
    # 1. Create via gcloud
    # 2. Verify via API
    # 3. Verify in database
    # All must match
    pass

def test_docker_container_lifecycle():
    """Test: Docker containers behave like real VMs (if compute service)"""
    # Create instance → container starts
    # Stop instance → container stops
    # Delete instance → container removed
    pass
```

### Test Running Workflow

```bash
# Whenever you modify code in {service}:

# Run tests immediately (before committing)
pytest tests/CloudTester/suites/{service}/ -v

# If new feature added:
pytest tests/CloudTester/suites/{service}/ -v --cov

# Before pushing to GitHub:
bash tests/run_full_suite.sh

# Your code cannot be committed if tests fail!
```

---

## 📐 Rule #4: Code Quality Standards

### Linting & Formatting

#### Python (Backend)
```bash
# Format code
black minimal-backend/

# Check linting
flake8 minimal-backend/ --max-line-length=100

# Type checking
mypy minimal-backend/

# All must pass before commit!
```

#### TypeScript/JavaScript (Frontend)
```bash
# Format code
npm run format

# Linting
npm run lint

# Type checking
npm run type-check

# All must pass before commit!
```

### Code Style Rules

#### Python
```python
# ✅ CORRECT
def create_instance(
    instance_name: str,
    machine_type: str,
    zone: str,
) -> Instance:
    """
    Create a new VM instance.
    
    Args:
        instance_name: Name of the instance
        machine_type: Machine type (e.g., e2-micro)
        zone: Zone (e.g., us-central1-a)
    
    Returns:
        Instance object
    
    Raises:
        ValueError: If instance_name already exists
    """
    # Implementation
    pass

# ❌ WRONG
def create_instance(name, type, zone):
    # Create instance
    pass
```

#### TypeScript
```typescript
// ✅ CORRECT
interface CreateInstanceRequest {
  instanceName: string;
  machineType: string;
  zone: string;
}

interface Instance {
  id: string;
  name: string;
  state: "PROVISIONING" | "RUNNING" | "STOPPED" | "TERMINATED";
  machineType: string;
  zone: string;
  createdAt: string;
}

async function createInstance(
  request: CreateInstanceRequest
): Promise<Instance> {
  // Implementation
}

// ❌ WRONG
async function createInstance(name, type, zone) {
  // Implementation
}
```

### Documentation Requirements

Every function must have:
- **Docstring** (Python) or **JSDoc** (TypeScript)
- **Parameter types**
- **Return type**
- **Error handling documented**

```python
# ✅ CORRECT
def delete_instance(instance_id: str) -> bool:
    """
    Delete a VM instance and its Docker container.
    
    Args:
        instance_id: Unique instance identifier
    
    Returns:
        True if deletion successful
    
    Raises:
        InstanceNotFoundError: If instance_id doesn't exist
        InstanceStillRunningError: If instance state is not STOPPED
    """
    pass
```

---

## 🔄 Rule #5: Git Workflow

### Branch Naming
```
✅ CORRECT:
  feature/compute-engine        (new service)
  fix/gcloud-list-output        (bug fix)
  docs/update-readme             (documentation)
  test/add-storage-tests         (test additions)

❌ WRONG:
  feature1
  fix-stuff
  my-changes
  update
```

### Commit Message Format
```
feature: {short description}

{detailed description if needed}

- {change 1}
- {change 2}
- {change 3}

Closes: #{issue_number}

Example:
─────────────────────────────
feat: implement cloud storage emulation

- Added gcloud storage wrapper commands (87.5% compatible)
- Implemented Storage API endpoints (create, list, delete, upload, download)
- Created React Storage management page with CRUD UI
- Added comprehensive test suite (92% coverage)
- Docker integration for object persistence

- gcloud commands: 10 commands
- API endpoints: 6 endpoints
- Test coverage: 92%

Closes: #42
─────────────────────────────
```

### Pre-Commit Checklist

Before committing, run:
```bash
# 1. Run all tests for the service
pytest tests/CloudTester/suites/{service}/ -v

# 2. Run linting
black minimal-backend/
flake8 minimal-backend/ --max-line-length=100

# 3. Format frontend code
cd gcp-stimulator-ui && npm run format

# 4. Check for console errors
npm run lint

# 5. Update documentation
# - CLAUDE.md (status)
# - README.md (if needed)
# - IMPLEMENTATION_TRACKER.md

# 6. Verify no files added to legacy/archived (cleanup only)

# 7. Only then commit!
git add .
git commit -m "feat: implement {service}"
```

---

## ⚠️ Rule #6: What NOT to Do

### ❌ DO NOT

1. **Skip gcloud CLI implementation**
   - "I'll add it later" → NOT ALLOWED
   - gcloud MUST come first

2. **Commit without tests passing**
   - "Tests will fail initially" → NOT ALLOWED
   - All tests must pass before commit

3. **Add features to legacy/ or archived/**
   - Those directories are for cleanup only
   - Add new features to main structure

4. **Push non-alphabetical function ordering**
   - "Readability is more important" → NOT ALLOWED
   - Alphabetical ordering is MANDATORY

5. **Mix services in one commit**
   - "I'll combine storage and compute" → NOT ALLOWED
   - One service = one feature branch/commit

6. **Modify existing tests without justification**
   - "They were wrong" → You need to document why
   - Tests are regression safeguards

7. **Deploy without full test coverage**
   - "It works locally" → NOT ENOUGH
   - Must pass: gcloud + API + integration tests

---

## 📊 Rule #7: Implementation Tracker

Update `IMPLEMENTATION_TRACKER.md` after each service:

```markdown
| Service | gcloud | API | Frontend | Tests | Status |
|---------|--------|-----|----------|-------|--------|
| Storage | ✅ 10 | ✅ 6 | ✅ | ✅ 92% | COMPLETE |
| Compute | ✅ 15 | ✅ 8 | ✅ | ✅ 89% | COMPLETE |
| {NewService} | ✅ X | ✅ Y | ✅ | ✅ Z% | COMPLETE |
```

---

## 🚀 Summary: Quick Checklist for New Service

```
Before touching code:
  ☐ Create feature branch: git checkout -b feature/{service}

Phase 1 - gcloud CLI (FIRST):
  ☐ Create: tests/CloudTester/wrappers/{service}.py
  ☐ Write wrapper functions (alphabetically ordered)
  ☐ Create: tests/CloudTester/suites/{service}/test_gcloud_cli.py
  ☐ Run: pytest tests/CloudTester/suites/{service}/test_gcloud_cli.py
  ☐ Coverage: ≥ 80%

Phase 2 - Backend API (SECOND):
  ☐ Create: minimal-backend/api/{service}.py
  ☐ Create: minimal-backend/services/{service}/
  ☐ Add models to: minimal-backend/database.py
  ☐ Create: tests/CloudTester/suites/{service}/test_api.py
  ☐ Run: pytest tests/CloudTester/suites/{service}/test_api.py
  ☐ Coverage: ≥ 85%

Phase 3 - Frontend (THIRD):
  ☐ Create: gcp-stimulator-ui/src/api/{service}.ts
  ☐ Create: gcp-stimulator-ui/src/pages/{ServiceName}.tsx
  ☐ Create: gcp-stimulator-ui/src/types/{service}.ts
  ☐ Add route to: gcp-stimulator-ui/src/App.tsx
  ☐ Manual testing: CRUD operations work
  ☐ No console errors

Phase 4 - Testing (FOURTH):
  ☐ Create: tests/CloudTester/suites/{service}/test_integration.py
  ☐ Run: pytest tests/CloudTester/suites/{service}/ -v --cov
  ☐ Coverage: ≥ 85%
  ☐ All tests pass

Before Commit:
  ☐ Run: black minimal-backend/ && flake8 minimal-backend/
  ☐ Run: npm run format && npm run lint
  ☐ Update: CLAUDE.md, IMPLEMENTATION_TRACKER.md
  ☐ Verify: No files added to legacy/ or archived/
  ☐ Git: Add, commit with proper message format

After Commit:
  ☐ Update: IMPLEMENTATION_TRACKER.md
  ☐ Update: README.md (if feature needs user documentation)
  ☐ Update: CONTEXT_CHECKPOINT.md
```

---

**Enforced by**: Development team  
**Review frequency**: After each new service  
**Last updated**: April 24, 2026
