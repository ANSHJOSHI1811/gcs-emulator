# CLEANUP_CHECKLIST.md

**Repository Cleanup & Organization Guide**

> **Purpose**: Remove clutter, organize legacy files, and maintain a clean codebase  
> **Status**: Ready for implementation  
> **Last Updated**: April 24, 2026  

---

## 🗑️ Phase 1: Identify Clutter

### Legacy Test Files (REMOVE or ARCHIVE)
```
tests/legacy/
├─ [OLD TEST FILES HERE]
└─ [DEPRECATED TESTS]

Action: ❌ DELETE or ARCHIVE
Reason: Outdated, not maintained, confuses new developers
```

**Cleanup Step 1**: 
```bash
# Backup first (just in case)
git add tests/legacy/
git commit -m "backup: archive legacy test files"

# Then remove from tracking (don't delete from git history)
git rm --cached tests/legacy/ -r
echo "tests/legacy/" >> .gitignore
git commit -m "chore: move legacy tests to gitignore"
```

---

### Archived Documentation (ORGANIZE, not delete)
```
docs/archived/
├─ old_research_1.md
├─ old_research_2.md
├─ deprecated_architecture.md
└─ [OUTDATED DOCS]

Action: ✅ KEEP but ORGANIZE
Reason: Historical value, might need reference
```

**Cleanup Step 2**:
```bash
# Organize into subdirectories
docs/archived/
  ├─ research/              (← create folder)
  │   ├─ old_research_1.md
  │   └─ old_research_2.md
  ├─ architecture/          (← create folder)
  │   ├─ deprecated_v1.md
  │   └─ deprecated_v2.md
  └─ README.md             (← create index)

# README.md content:
# Archived Documentation
# This folder contains historical docs and research.
# 
# - research/ - Old research and spike notes
# - architecture/ - Outdated architecture docs
#
# Current docs are in ../
```

---

### Unused Configuration Files
```
Scan for:
├─ .env files (old, unused)
├─ config files for old services
├─ Old deployment configs
├─ Unused Docker files
└─ Old test runner scripts

Example locations to check:
  - Root directory (*.env.*)
  - minimal-backend/ (old config.py, unused imports)
  - gcp-stimulator-ui/ (old build scripts, unused configs)
  - tests/ (old runner scripts, deprecated wrappers)
```

**Cleanup Step 3**: Audit and remove unused configs

```bash
# Find all .env files
find . -name ".env*" -type f

# Check git history for most recent
git log --oneline --all -- ".env*"

# If old, remove:
git rm --cached .env.old
echo ".env.old" >> .gitignore
git commit -m "chore: remove unused .env files"
```

---

### Unused Dependencies
```
minimal-backend/requirements.txt
gcp-stimulator-ui/package.json

Action: ❌ REMOVE unused imports
```

**Cleanup Step 4**: Audit dependencies

```bash
# Python - Check for unused imports
cd minimal-backend
pip install autoflake
autoflake --recursive --remove-all-unused-imports . --check

# JavaScript - Check for unused packages
cd ../gcp-stimulator-ui
npm ls --all
# Remove unused: npm uninstall {package}
```

---

## 📁 Phase 2: Organize Directory Structure

### Backend Organization

**Current (Messy)**:
```
minimal-backend/
├─ main.py
├─ database.py
├─ docker_manager.py
├─ api/                    ← Mixed services here
├─ services/               ← Business logic
├─ core/
├─ utils/
├─ migrations/             (← might be missing)
├─ config/                 (← might need)
└─ requirements.txt
```

**Target (Clean)**:
```
minimal-backend/
├─ app/
│   ├─ __init__.py
│   ├─ main.py            ← App initialization
│   ├─ config.py          ← Environment & config
│   │
│   ├─ api/               ← API routes
│   │   ├─ __init__.py
│   │   ├─ autoscaling.py
│   │   ├─ compute.py
│   │   ├─ firewall.py
│   │   ├─ gke.py
│   │   ├─ iam.py
│   │   ├─ monitoring.py
│   │   ├─ projects.py
│   │   ├─ routes.py
│   │   ├─ storage.py
│   │   └─ vpc.py
│   │
│   ├─ services/          ← Business logic
│   │   ├─ __init__.py
│   │   ├─ autoscaling/
│   │   ├─ compute/
│   │   ├─ storage/
│   │   ├─ vpc/
│   │   ├─ iam/
│   │   ├─ monitoring/
│   │   └─ base.py        ← Shared base class
│   │
│   ├─ models/            ← Database models
│   │   ├─ __init__.py
│   │   ├─ autoscaling.py
│   │   ├─ compute.py
│   │   ├─ storage.py
│   │   ├─ vpc.py
│   │   └─ base.py        ← Base model class
│   │
│   ├─ core/              ← Shared utilities
│   │   ├─ __init__.py
│   │   ├─ database.py    ← DB connection & session
│   │   ├─ docker.py      ← Docker manager
│   │   └─ exceptions.py  ← Custom exceptions
│   │
│   └─ utils/             ← Helper functions
│       ├─ __init__.py
│       ├─ validators.py
│       ├─ formatters.py
│       └─ helpers.py
│
├─ migrations/            ← DB migrations (if using Alembic)
│   └─ versions/
│
├─ tests/                 ← Unit tests (if any)
│
├─ requirements.txt
├─ .env.example          ← Template for .env
├─ .flake8               ← Python linting config
├─ pyproject.toml        ← Python project config
└─ README.md
```

**Cleanup Steps for Backend**:

```bash
# 1. Create new structure
mkdir -p minimal-backend/app/api
mkdir -p minimal-backend/app/services
mkdir -p minimal-backend/app/models
mkdir -p minimal-backend/app/core
mkdir -p minimal-backend/app/utils

# 2. Move files (example)
mv minimal-backend/main.py minimal-backend/app/
mv minimal-backend/database.py minimal-backend/app/models/
mv minimal-backend/docker_manager.py minimal-backend/app/core/docker.py
mv minimal-backend/api/* minimal-backend/app/api/
mv minimal-backend/services/* minimal-backend/app/services/

# 3. Create __init__.py files
touch minimal-backend/app/__init__.py
touch minimal-backend/app/api/__init__.py
touch minimal-backend/app/services/__init__.py
touch minimal-backend/app/models/__init__.py
touch minimal-backend/app/core/__init__.py
touch minimal-backend/app/utils/__init__.py

# 4. Update imports in main.py
# Change: from database import Base
# To:     from app.models.base import Base

# 5. Test that it still works
cd minimal-backend && python main.py

# 6. Commit
git add minimal-backend/
git commit -m "refactor: reorganize backend structure"
```

---

### Frontend Organization

**Current (Messy)**:
```
gcp-stimulator-ui/src/
├─ pages/
├─ components/
├─ api/
├─ contexts/
├─ hooks/
├─ types/
├─ utils/
├─ config/
├─ layouts/
├─ App.tsx
└─ main.tsx
```

**Target (Same, but Clean Files)**:
```
gcp-stimulator-ui/
├─ src/
│   ├─ pages/
│   │   ├─ Autoscaling.tsx      ← Service pages
│   │   ├─ Compute.tsx
│   │   ├─ Firewall.tsx
│   │   ├─ GKE.tsx              (← might not exist yet)
│   │   ├─ IAM.tsx
│   │   ├─ Monitoring.tsx
│   │   ├─ NotFound.tsx
│   │   ├─ Routes.tsx
│   │   ├─ Storage.tsx
│   │   └─ VPC.tsx
│   │
│   ├─ components/              ← Reusable UI components
│   │   ├─ common/
│   │   │   ├─ Button.tsx
│   │   │   ├─ Modal.tsx
│   │   │   ├─ Table.tsx
│   │   │   └─ Input.tsx
│   │   ├─ layout/
│   │   │   ├─ Sidebar.tsx
│   │   │   ├─ Header.tsx
│   │   │   └─ Footer.tsx
│   │   └─ forms/
│   │       ├─ CreateInstanceForm.tsx
│   │       └─ CreateBucketForm.tsx
│   │
│   ├─ api/                     ← API clients
│   │   ├─ autoscaling.ts
│   │   ├─ compute.ts
│   │   ├─ gke.ts
│   │   ├─ iam.ts
│   │   ├─ monitoring.ts
│   │   ├─ routes.ts
│   │   ├─ storage.ts
│   │   └─ vpc.ts
│   │
│   ├─ types/                   ← TypeScript interfaces
│   │   ├─ autoscaling.ts
│   │   ├─ compute.ts
│   │   ├─ gke.ts
│   │   ├─ iam.ts
│   │   ├─ monitoring.ts
│   │   ├─ routes.ts
│   │   ├─ storage.ts
│   │   └─ vpc.ts
│   │
│   ├─ contexts/                ← React Context providers
│   │   ├─ AuthContext.tsx
│   │   ├─ ProjectContext.tsx
│   │   └─ NotificationContext.tsx
│   │
│   ├─ hooks/                   ← Custom React hooks
│   │   ├─ useAuth.ts
│   │   ├─ useProject.ts
│   │   ├─ useNotification.ts
│   │   └─ useFetch.ts
│   │
│   ├─ layouts/                 ← Page layouts
│   │   └─ MainLayout.tsx
│   │
│   ├─ utils/                   ← Helper functions
│   │   ├─ formatters.ts
│   │   ├─ validators.ts
│   │   └─ helpers.ts
│   │
│   ├─ config/                  ← Configuration
│   │   ├─ constants.ts
│   │   ├─ api.ts               ← API base URL, etc
│   │   └─ theme.ts
│   │
│   ├─ App.tsx                  ← Main app component
│   ├─ main.tsx                 ← Entry point
│   └─ vite-env.d.ts            ← Vite type definitions
│
├─ public/                       ← Static assets
├─ vite.config.ts
├─ tsconfig.json
├─ tailwind.config.js
├─ tailwind.config.ts
├─ package.json
├─ .env.example
├─ .eslintrc.json
└─ README.md
```

**Cleanup Steps for Frontend**:

```bash
# Frontend is mostly clean already, just:

# 1. Remove any duplicate config files (tailwind.config.ts vs .js)
rm -f gcp-stimulator-ui/tailwind.config.js  # Keep only .ts version

# 2. Create .env.example if missing
cat > gcp-stimulator-ui/.env.example << 'EOF'
VITE_API_BASE_URL=http://localhost:8080
VITE_API_TIMEOUT=30000
EOF

# 3. Ensure all pages are in src/pages/
# Ensure all API clients are in src/api/
# Ensure all types are in src/types/

# 4. Commit
git add gcp-stimulator-ui/
git commit -m "chore: cleanup frontend structure"
```

---

### Test Organization

**Current (Messy)**:
```
tests/
├─ CloudTester/
│   ├─ suites/
│   │   ├─ autoscaling/
│   │   ├─ compute/
│   │   ├─ firewall/
│   │   ├─ gke/
│   │   ├─ iam/
│   │   ├─ monitoring/
│   │   ├─ routes/
│   │   ├─ storage/
│   │   └─ vpc/
│   │
│   ├─ wrappers/
│   │   ├─ autoscaling.py
│   │   ├─ compute.py
│   │   ├─ iam.py
│   │   ├─ monitoring.py
│   │   ├─ storage.py
│   │   └─ vpc.py
│   │
│   ├─ base/
│   │   └─ test_base.py
│   │
│   └─ scripts/
│       └─ run_full_suite.sh
│
├─ legacy/
│   └─ [OLD TEST FILES]
│
└─ pytest.ini
```

**Target (Clean)**:
```
tests/
├─ conftest.py              ← Global pytest fixtures
├─ pytest.ini
│
├─ unit/                    ← Unit tests
│   ├─ __init__.py
│   ├─ test_validators.py
│   ├─ test_formatters.py
│   └─ test_helpers.py
│
├─ integration/             ← Integration tests
│   ├─ __init__.py
│   ├─ autoscaling/
│   ├─ compute/
│   ├─ firewall/
│   ├─ gke/
│   ├─ iam/
│   ├─ monitoring/
│   ├─ routes/
│   ├─ storage/
│   └─ vpc/
│
├─ fixtures/                ← Test fixtures & data
│   ├─ __init__.py
│   ├─ database_fixtures.py
│   ├─ docker_fixtures.py
│   └─ gcp_fixtures.py
│
├─ mocks/                   ← Mock objects
│   ├─ __init__.py
│   ├─ gcloud_mock.py
│   └─ docker_mock.py
│
├─ gcloud_wrappers/         ← gcloud CLI wrappers (moved from CloudTester)
│   ├─ __init__.py
│   ├─ autoscaling.py
│   ├─ compute.py
│   ├─ iam.py
│   ├─ monitoring.py
│   ├─ storage.py
│   └─ vpc.py
│
└─ scripts/
    ├─ run_all_tests.sh     ← Renamed from run_full_suite.sh
    ├─ run_integration_tests.sh
    ├─ run_unit_tests.sh
    └─ generate_coverage_report.sh
```

**Cleanup Steps for Tests**:

```bash
# 1. Reorganize test files
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/fixtures
mkdir -p tests/mocks
mkdir -p tests/gcloud_wrappers

# 2. Move wrappers from CloudTester
mv tests/CloudTester/wrappers/* tests/gcloud_wrappers/
rmdir tests/CloudTester/wrappers

# 3. Move test suites
mv tests/CloudTester/suites/* tests/integration/
rmdir tests/CloudTester/suites

# 4. Move base fixtures
mv tests/CloudTester/base/* tests/fixtures/
# If using test_base.py, rename to conftest.py
cp tests/fixtures/test_base.py tests/conftest.py

# 5. Create __init__.py files
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/fixtures/__init__.py
touch tests/mocks/__init__.py
touch tests/gcloud_wrappers/__init__.py

# 6. Update pytest.ini to point to correct locations
cat > tests/pytest.ini << 'EOF'
[pytest]
testpaths = tests/unit tests/integration
python_files = test_*.py
python_classes = Test*
python_functions = test_*
EOF

# 7. Update run scripts
cat > tests/scripts/run_all_tests.sh << 'EOF'
#!/bin/bash
cd tests
pytest unit/ integration/ -v --cov=../minimal-backend --cov-report=html
EOF

chmod +x tests/scripts/run_all_tests.sh

# 8. Commit
git add tests/
git commit -m "refactor: reorganize test structure"
```

---

## 🗄️ Phase 3: Cleanup & Remove Legacy

### Step 1: Remove Legacy Test Files
```bash
# Only if they're truly not needed (back up first!)
git rm -r tests/legacy/
git commit -m "chore: remove legacy test files"
echo "tests/legacy/" >> .gitignore
git commit -m "chore: ignore legacy directory"
```

### Step 2: Remove Unused Patches
```bash
# If patches/ contains old, unused patches:
ls -la patches/

# If empty or unused:
rm -rf patches/
git rm -r patches/
git commit -m "chore: remove unused patches"
```

### Step 3: Clean .gitignore
```bash
# Review and update .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local
.env.*.local

# Test/Coverage
.pytest_cache/
.coverage
htmlcov/
.tox/

# Frontend
node_modules/
dist/
.turbo/
*.log

# Database
*.db
*.sqlite
*.sqlite3

# Docker
.docker/

# OS
*.tar.gz
*.zip

# Legacy (for cleanup phase)
tests/legacy/

# Project-specific
/tmp/gcs-storage/
EOF

git add .gitignore
git commit -m "chore: update .gitignore"
```

---

## 📝 Phase 4: Documentation & README Updates

### Update Root README.md
```markdown
# GCS Emulator

A comprehensive Google Cloud Platform (GCP) emulator that simulates GCP services locally.

## Quick Start

### Prerequisites
- Docker (running)
- Python 3.9+
- Node.js 16+
- PostgreSQL (AWS RDS)

### Setup

1. **Backend**:
   ```bash
   cd minimal-backend
   pip install -r requirements.txt
   export DATABASE_URL=postgresql://user:pass@host:5432/db
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

2. **Frontend**:
   ```bash
   cd gcp-stimulator-ui
   npm install
   npm run dev
   ```

3. **Access**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8080
   - API Docs: http://localhost:8080/docs

## Documentation

- [CLAUDE.md](./CLAUDE.md) - Project context (for AI agents)
- [DEVELOPMENT_RULES.md](./DEVELOPMENT_RULES.md) - Development workflow
- [SKILLS_ROADMAP.md](./SKILLS_ROADMAP.md) - AI agent knowledge requirements
- [IMPLEMENTATION_TRACKER.md](./IMPLEMENTATION_TRACKER.md) - Feature status

## Services Implemented

- ✅ Cloud Storage
- ✅ Compute Engine
- ✅ VPC Networks
- ✅ IAM
- ✅ Cloud Monitoring
- ⚠️ Autoscaling (partial)
- ⚠️ GKE (partial)
- ⚠️ Firewall (partial)

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific service tests
pytest tests/integration/compute/ -v

# With coverage
pytest tests/ -v --cov=minimal-backend --cov-report=html
```

## Contributing

See [DEVELOPMENT_RULES.md](./DEVELOPMENT_RULES.md) for workflow guidelines.

## License

MIT
```

---

## ✅ Phase 5: Final Verification

**After cleanup, verify**:

```bash
# 1. Project still builds/runs
cd minimal-backend && python -c "from app.main import app; print('✅ Backend imports OK')"
cd ../gcp-stimulator-ui && npm run build

# 2. Tests still run
pytest tests/ -v --tb=short

# 3. No broken imports
python -c "import ast; ast.parse(open('minimal-backend/app/main.py').read())"

# 4. Git is clean
git status  # Should be clean after all commits

# 5. Documentation is complete
ls -la CLAUDE.md DEVELOPMENT_RULES.md SKILLS_ROADMAP.md IMPLEMENTATION_TRACKER.md
```

---

## 📋 Cleanup Checklist

Use this as your action plan:

```
PHASE 1: Identify Clutter
  ☐ List legacy test files (tests/legacy/)
  ☐ List archived docs (docs/archived/)
  ☐ Find unused config files
  ☐ Audit dependencies (requirements.txt, package.json)

PHASE 2: Organize Structure
  ☐ Create new directory structure (backend)
  ☐ Move files to proper locations (backend)
  ☐ Create __init__.py files (backend)
  ☐ Update imports in main.py
  ☐ Test backend still works
  ☐ Reorganize test directory
  ☐ Verify frontend structure (mostly clean)

PHASE 3: Remove Legacy
  ☐ Remove tests/legacy/ (after backup)
  ☐ Remove patches/ (if unused)
  ☐ Remove old .env files
  ☐ Remove unused imports from requirements.txt

PHASE 4: Documentation
  ☐ Update README.md
  ☐ Ensure CLAUDE.md is current
  ☐ Ensure DEVELOPMENT_RULES.md exists
  ☐ Ensure SKILLS_ROADMAP.md exists
  ☐ Update IMPLEMENTATION_TRACKER.md

PHASE 5: Verification
  ☐ Backend imports work
  ☐ Frontend builds
  ☐ Tests run
  ☐ Git is clean
  ☐ Documentation complete

FINAL: Commit Cleanup
  ☐ git add .
  ☐ git commit -m "chore: cleanup and reorganize repository"
  ☐ Push to GitHub
  ☐ Update CONTEXT_CHECKPOINT.md
```

---

**Time Estimate**: 2-4 hours  
**Difficulty**: Medium (mostly moving files and updating imports)  
**Risk**: Low (all changes can be reverted via git)

---

**Last Updated**: April 24, 2026  
**Next**: After cleanup, create service implementation checklist
