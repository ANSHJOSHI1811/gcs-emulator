# 🤖 PROMPT FOR AI AGENT: Repository Cleanup & Organization

Copy this entire prompt and give it to Claude (or your AI agent) to organize your repo.

---

## 📋 TASK: Organize & Cleanup GCS Emulator Repository

**Objective**: Clean up the messy GCS Emulator repo, organize files properly, and remove unwanted branches.

**Current Status**: 
- Repo has scattered legacy files, old tests, unused branches
- Directory structure needs reorganization
- Needs cleanup before starting new development

**Expected Outcome**:
- ✅ Clean, organized directory structure
- ✅ Legacy files archived/removed
- ✅ Unwanted branches deleted
- ✅ Code still works after cleanup
- ✅ Tests pass after cleanup
- ✅ Ready for confident development

---

## 🎯 YOUR ROLE (AI Agent)

You are helping organize a GCP emulator codebase. You have these documents as reference:

1. **CLAUDE.md** - Current project status
2. **DEVELOPMENT_RULES.md** - Development standards
3. **SKILLS_ROADMAP.md** - Knowledge base
4. **CLEANUP_CHECKLIST.md** - Detailed cleanup steps

Your job is to follow CLEANUP_CHECKLIST.md exactly and clean up the repository.

---

## 📂 PHASE 1: Analyze Current Repository Structure

### STEP 1.1: Scan Backend Structure
List the current backend directory structure:
```bash
find minimal-backend/ -type f -name "*.py" | head -30
tree minimal-backend/ -L 3 --dirsfirst
```

**Questions to answer**:
- [ ] Where are files currently located? (in root or organized?)
- [ ] Are there __init__.py files in all directories?
- [ ] What files are in minimal-backend/ root that should be in subdirectories?
- [ ] Any duplicate files or unclear naming?

### STEP 1.2: Scan Test Structure
List the current test directory structure:
```bash
find tests/ -type f -name "*.py" | head -20
tree tests/ -L 3 --dirsfirst
```

**Questions to answer**:
- [ ] Where are test files? (CloudTester/suites, CloudTester/wrappers, etc)
- [ ] Are there legacy/ files that could be removed?
- [ ] Any duplicate test files?
- [ ] gcloud wrappers location?

### STEP 1.3: Check Git Branches
List all branches:
```bash
git branch -a
git log --all --oneline | head -20
```

**Questions to answer**:
- [ ] What branches exist?
- [ ] Which are active (recently committed)?
- [ ] Which are old/unused?
- [ ] Current branch?
- [ ] List branches to DELETE (old, abandoned, merged)

### STEP 1.4: Check for Clutter Files
```bash
ls -la minimal-backend/ | grep -E "\.(env|config|old|backup)"
ls -la gcp-stimulator-ui/ | grep -E "\.(env|config|old|backup)"
ls -la . | grep -E "\.env|\.backup|old_|legacy"
find . -type f -name "*.bak" -o -name "*.old" -o -name "*backup*"
```

**List found**:
- [ ] Unused .env files
- [ ] Old config files
- [ ] Backup files
- [ ] Any other clutter

---

## 🗑️ PHASE 2: Cleanup Branches

### STEP 2.1: Identify Unwanted Branches

For each branch, ask:
- Is it merged to main/master?
- Has it been updated recently (last 3 months)?
- Is it actively used?

**Safe to DELETE branches**:
- ✅ Already merged (git branch --merged)
- ✅ Old and abandoned (no commits in 3+ months)
- ✅ Duplicate functionality

**DO NOT DELETE**:
- ❌ main / master (primary branch)
- ❌ feature/cloud-monitoring (if active)
- ❌ develop / staging (if used)

### STEP 2.2: Create Backup Branch (SAFETY)
```bash
git branch backup/before-cleanup-$(date +%Y-%m-%d)
git push origin backup/before-cleanup-$(date +%Y-%m-%d)
```

**DO THIS FIRST** - Allows rollback if needed.

### STEP 2.3: Delete Unwanted Branches

**Get list of merged branches**:
```bash
git branch --merged main  # or master, depending on your primary branch
```

**Delete safely**:
```bash
git branch -d {branch_name}  # Only deletes if merged
git push origin --delete {branch_name}  # Remove from GitHub
```

**For abandoned branches** (not merged but old):
```bash
git branch -D {branch_name}  # Force delete
git push origin --delete {branch_name}
```

### STEP 2.4: Verify Cleanup
```bash
git branch -a  # List all remaining branches
git log --all --oneline | head -10  # Verify history intact
```

---

## 📁 PHASE 3: Reorganize Backend Structure

### STEP 3.1: Create New Structure

Create these directories (if don't exist):
```bash
mkdir -p minimal-backend/app/api
mkdir -p minimal-backend/app/services
mkdir -p minimal-backend/app/models
mkdir -p minimal-backend/app/core
mkdir -p minimal-backend/app/utils
mkdir -p minimal-backend/tests/unit
mkdir -p minimal-backend/tests/fixtures
mkdir -p minimal-backend/migrations
```

### STEP 3.2: Move Backend Files

**Current structure** → **New structure**:

```bash
# Main application files
mv minimal-backend/main.py minimal-backend/app/ || echo "main.py already moved"

# Database & models (if database.py exists)
mv minimal-backend/database.py minimal-backend/app/models/ || echo "database.py not found"
# Then create models/__init__.py that imports from database.py for compatibility

# Docker manager
mv minimal-backend/docker_manager.py minimal-backend/app/core/ || echo "docker_manager.py not found"

# API files (should be in api/ already, but verify)
if [ -d minimal-backend/api ]; then
  mv minimal-backend/api/* minimal-backend/app/api/ || echo "api files already moved"
  rmdir minimal-backend/api
fi

# Services (should be in services/ already, but verify)
if [ -d minimal-backend/services ]; then
  mv minimal-backend/services/* minimal-backend/app/services/ || echo "services already moved"
  rmdir minimal-backend/services
fi

# Core utilities
if [ -d minimal-backend/core ] && [ ! -d minimal-backend/app/core ]; then
  mv minimal-backend/core/* minimal-backend/app/core/ || true
  rmdir minimal-backend/core
fi
```

### STEP 3.3: Create __init__.py Files

Create empty __init__.py in all directories:
```bash
touch minimal-backend/app/__init__.py
touch minimal-backend/app/api/__init__.py
touch minimal-backend/app/services/__init__.py
touch minimal-backend/app/models/__init__.py
touch minimal-backend/app/core/__init__.py
touch minimal-backend/app/utils/__init__.py
```

### STEP 3.4: Update Imports in main.py

In `minimal-backend/app/main.py`, update all imports:

**OLD** → **NEW**:
```python
# OLD
from database import Base, get_db
from docker_manager import DockerManager
from api import storage, compute, vpc

# NEW
from app.models.database import Base, get_db
from app.core.docker import DockerManager
from app.api import storage, compute, vpc
```

Search for and replace all import statements that reference old paths.

### STEP 3.5: Update requirements.txt Import Path (if any)

Check if any relative imports in code. Fix to absolute:
```python
# OLD
from .database import Base

# NEW  
from app.models.database import Base
```

### STEP 3.6: Test Backend Still Works

```bash
cd minimal-backend

# Check imports
python -c "from app.main import app; print('✅ Backend imports successful')"

# Run dev server briefly
timeout 5 uvicorn app.main:app --reload --host 0.0.0.0 --port 8080 || true

# Check for import errors
python -m py_compile app/main.py
python -m py_compile app/models/database.py
python -m py_compile app/core/docker.py
```

**Expected**: No import errors, server starts without errors (even if timeout).

---

## 🧪 PHASE 4: Reorganize Test Structure

### STEP 4.1: Create New Test Structure

```bash
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/fixtures
mkdir -p tests/mocks
mkdir -p tests/gcloud_wrappers
mkdir -p tests/scripts
```

### STEP 4.2: Move gcloud Wrappers

If gcloud wrappers in CloudTester/wrappers/:
```bash
# Move wrappers
if [ -d tests/CloudTester/wrappers ]; then
  mv tests/CloudTester/wrappers/* tests/gcloud_wrappers/ || true
  # Keep a README in gcloud_wrappers
  cat > tests/gcloud_wrappers/README.md << 'EOF'
# gcloud CLI Wrappers

These files contain Python wrappers for gcloud CLI commands.
Used for testing gcloud compatibility with our emulator.

- compute.py - gcloud compute commands
- storage.py - gcloud storage commands
- vpc.py - gcloud compute networks commands
- iam.py - gcloud iam commands
- monitoring.py - gcloud monitoring commands
EOF
fi
```

### STEP 4.3: Move Test Suites

If test suites in CloudTester/suites/:
```bash
# Move test suites to integration/
if [ -d tests/CloudTester/suites ]; then
  mv tests/CloudTester/suites/* tests/integration/ || true
fi
```

### STEP 4.4: Move Fixtures

If base test fixtures:
```bash
# Move fixtures
if [ -d tests/CloudTester/base ]; then
  mv tests/CloudTester/base/* tests/fixtures/ || true
fi
```

### STEP 4.5: Create __init__.py Files

```bash
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/fixtures/__init__.py
touch tests/mocks/__init__.py
touch tests/gcloud_wrappers/__init__.py
```

### STEP 4.6: Update pytest.ini

Create/update `tests/pytest.ini`:
```ini
[pytest]
testpaths = tests/unit tests/integration
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers -v
EOF
```

Or place at root `pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers -v
```

### STEP 4.7: Test Tests Still Work

```bash
# Run a simple test to verify structure
pytest tests/integration/ -v --collect-only  # Just list tests, don't run

# If that fails, check for import issues
python -m pytest tests/ --co -q

# Fix any import errors in test files
```

---

## 🗑️ PHASE 5: Remove Legacy & Clutter

### STEP 5.1: Remove Legacy Tests

**Only if safe** (check git history first):
```bash
# Backup
git status  # Ensure no uncommitted changes
git stash  # Stash any uncommitted work

# Check if legacy tests are referenced anywhere
grep -r "legacy" . --include="*.py" --include="*.md" || echo "No references to legacy"

# Remove if safe
if [ -d tests/legacy ]; then
  rm -rf tests/legacy
  echo "tests/legacy/" >> .gitignore
  git add .gitignore
  echo "✅ Removed tests/legacy/"
fi
```

### STEP 5.2: Remove CloudTester Directory (if moved everything)

```bash
# Only if everything is moved out
if [ -d tests/CloudTester ]; then
  if [ -z "$(ls -A tests/CloudTester)" ]; then
    rm -rf tests/CloudTester
    echo "✅ Removed empty tests/CloudTester/"
  else
    echo "⚠️ tests/CloudTester still has files, keeping it"
    ls -la tests/CloudTester/
  fi
fi
```

### STEP 5.3: Remove Unused .env Files

```bash
# Find old .env files
find . -name ".env.*" -o -name "*.env.bak" -o -name ".env.old"

# Remove if old
find . -name ".env.*.bak" -delete
find . -name ".env.old" -delete

# Keep only .env.example and .env-gcloud
# Remove others if not needed
```

### STEP 5.4: Update .gitignore

```bash
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

# Legacy (for cleanup)
tests/legacy/
tests/CloudTester/

# Project-specific
/tmp/gcs-storage/
EOF

git add .gitignore
```

### STEP 5.5: Remove Old Config Files

```bash
# Find and remove old configs
find . -name "*.old" -o -name "*.bak" -o -name "*backup*" | xargs rm -f

# Remove if found
[ -f "minimal-backend/old_config.py" ] && rm minimal-backend/old_config.py
[ -f "minimal-backend/config.backup.py" ] && rm minimal-backend/config.backup.py
```

---

## ✅ PHASE 6: Verification & Testing

### STEP 6.1: Verify Backend Works

```bash
cd minimal-backend

# 1. Check imports
python -c "from app.main import app; print('✅ Backend imports OK')" || exit 1

# 2. Check all modules
python -c "from app.models import database; print('✅ Models OK')" || exit 1
python -c "from app.core import docker; print('✅ Core OK')" || exit 1
python -c "from app.api import compute, storage; print('✅ API OK')" || exit 1
python -c "from app.services import compute, storage; print('✅ Services OK')" || exit 1

# 3. Try to start server (timeout after 3 seconds)
timeout 3 uvicorn app.main:app --reload --host 0.0.0.0 --port 8080 || echo "Server startup test done"

echo "✅ Backend verification complete"
```

### STEP 6.2: Verify Frontend Works

```bash
cd ../gcp-stimulator-ui

# 1. Check dependencies
npm list | head -20

# 2. Verify build
npm run build || exit 1

# 3. Verify linting
npm run lint || echo "⚠️ Linting errors (fix manually if needed)"

echo "✅ Frontend verification complete"
```

### STEP 6.3: Verify Tests Still Work

```bash
cd ../tests

# 1. Collect tests
pytest --collect-only -q | head -20

# 2. Run a quick test (if any exist)
pytest tests/integration/storage/test_api.py -v --maxfail=1 2>/dev/null || echo "Tests need review"

echo "✅ Test structure verified"
```

### STEP 6.4: Check Git Status

```bash
git status

# Should show:
# - New files/directories created
# - Deleted legacy files
# - No red flags

# Verify git still works
git log --oneline | head -5
```

---

## 📝 PHASE 7: Commit Changes

### STEP 7.1: Review Changes Before Commit

```bash
git status  # What changed?
git diff --stat  # Summary of changes

# Review large deletions
git diff --name-status | grep "^D"  # Deleted files
```

### STEP 7.2: Stage Changes

```bash
# Stage all changes
git add -A

# Verify staging
git status  # Check "Changes to be committed"
```

### STEP 7.3: Commit with Proper Message

```bash
git commit -m "refactor: reorganize repository structure and cleanup

Backend Reorganization:
  - Create app/ structure (api/, services/, models/, core/, utils/)
  - Move main.py to app/
  - Move database.py to app/models/
  - Move docker_manager.py to app/core/
  - Update all imports for new structure

Test Reorganization:
  - Create tests/ subdirectories (unit/, integration/, fixtures/, gcloud_wrappers/)
  - Move gcloud wrappers to tests/gcloud_wrappers/
  - Move test suites to tests/integration/
  - Move fixtures to tests/fixtures/
  - Update pytest configuration

Cleanup:
  - Remove tests/legacy/ directory
  - Remove old .env files
  - Update .gitignore for new structure
  - Remove empty directories

Verification:
  - ✅ Backend imports work
  - ✅ Frontend builds successfully
  - ✅ Test structure verified
  - ✅ Git history intact

This prepares repo for confident development with AI agents."
```

### STEP 7.4: Verify Commit

```bash
git log --oneline | head -5  # New commit at top?
git show HEAD --stat  # What was in commit?
```

---

## 🌿 PHASE 8: Cleanup Branches (Final)

### STEP 8.1: List Branches to Delete

Based on your knowledge:
- `feature/cloud-monitoring` - Is this active or done?
- Any old branches from months ago?
- Any duplicate branches?

**Ask me (you, the user)**: Which branches should be deleted?

For now, follow this safe approach:

```bash
# Delete only merged branches (safe)
git branch --merged main | grep -v " main" | xargs git branch -d

# List remaining branches
git branch -a
```

### STEP 8.2: Delete Unwanted Branches

**After confirming with you** which to delete:

```bash
# Delete locally
git branch -d {branch_name}

# Delete on GitHub
git push origin --delete {branch_name}

# Example for old branches:
git branch -d feature/old-work
git push origin --delete feature/old-work
```

### STEP 8.3: Verify Final Branch State

```bash
git branch -a  # List all
git branch -v  # List with last commit info
```

---

## 📋 FINAL CHECKLIST

Before saying "DONE", verify ALL of these:

```
Backend Organization:
  ☐ minimal-backend/app/ directory exists
  ☐ All .py files moved to proper locations
  ☐ All __init__.py files created
  ☐ Imports updated in main.py
  ☐ Backend starts without errors
  ☐ No import errors when testing imports

Frontend:
  ☐ npm run build succeeds
  ☐ npm run lint passes (or noted for manual fix)
  ☐ Frontend code unchanged

Tests:
  ☐ tests/gcloud_wrappers/ exists with wrappers
  ☐ tests/integration/ exists with test suites
  ☐ tests/fixtures/ exists
  ☐ pytest.ini configured correctly
  ☐ Test discovery works (pytest --collect-only)

Cleanup:
  ☐ tests/legacy/ removed (if not needed)
  ☐ CloudTester/ moved/removed
  ☐ Old .env files removed
  ☐ .gitignore updated
  ☐ No leftover backup files

Git:
  ☐ Backup branch created (backup/before-cleanup-YYYY-MM-DD)
  ☐ Changes committed with proper message
  ☐ No uncommitted changes
  ☐ Log shows new commit
  ☐ Unwanted branches deleted

Documentation:
  ☐ CLAUDE.md in root
  ☐ DEVELOPMENT_RULES.md in root
  ☐ SKILLS_ROADMAP.md in root
  ☐ CLEANUP_CHECKLIST.md in root
  ☐ IMPLEMENTATION_TRACKER.md updated (if changed)

Final Verification:
  ☐ Run: python -c "from app.main import app" → No errors
  ☐ Run: cd gcp-stimulator-ui && npm run build → Success
  ☐ Run: pytest tests/ --collect-only → Tests found
  ☐ Run: git status → Clean (nothing to commit)
```

---

## 🎯 SUMMARY OF WHAT YOU'LL GET

After this cleanup, you'll have:

✅ **Organized Backend**
- Clean structure: app/api/, app/services/, app/models/, app/core/, app/utils/
- All imports updated
- Code still works

✅ **Organized Tests**
- gcloud wrappers in tests/gcloud_wrappers/
- Test suites in tests/integration/
- Fixtures in tests/fixtures/
- pytest configured

✅ **Cleaned Repository**
- Legacy files removed
- Old branches deleted
- .gitignore updated
- No clutter

✅ **Git Ready**
- Clean history
- Backup branch created
- New cleanup commit
- Ready for development

✅ **Documentation In Place**
- CLAUDE.md, DEVELOPMENT_RULES.md, SKILLS_ROADMAP.md ready
- Ready for AI agent collaboration

---

## ⚠️ IMPORTANT NOTES FOR AI AGENT

1. **Ask for Confirmation**: Before deleting branches, ask which ones to delete
2. **Backup First**: Always create backup branch before major changes
3. **Test Frequently**: After moving files, test imports
4. **Slow and Steady**: Better to be careful than break everything
5. **Ask for Help**: If confused, ask (the user) for clarification
6. **Verify Each Phase**: Don't skip verification steps

---

## 📞 IF SOMETHING BREAKS

**Rollback instantly**:
```bash
# If things go wrong, rollback to backup branch
git reset --hard backup/before-cleanup-YYYY-MM-DD

# Or just revert last commit
git revert HEAD

# Or revert to before you started
git log --oneline | grep "refactor: reorganize"
git reset --hard {commit_before_cleanup}
```

---

**Ready?** Give this prompt to your AI agent! 🚀

They will:
1. Analyze current structure
2. Organize backend files
3. Reorganize test structure
4. Remove clutter
5. Test everything works
6. Delete unwanted branches
7. Commit with proper message
8. Verify final state

**Estimated Time**: 1-2 hours for a complete cleanup

**Difficulty**: Medium (mostly file moving, import fixing)

**Risk**: Low (git history protected, can rollback anytime)

