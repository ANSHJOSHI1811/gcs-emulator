# ⚡ QUICK START: Repo Cleanup with AI Agent

**Time to execute**: 1-2 hours  
**Difficulty**: Medium  
**Risk**: Low (git history protected)

---

## 🚀 HOW TO USE THIS

### Step 1: Prepare Your Repo
```bash
# Go to your GCS Emulator repo
cd your-gcs-emulator-repo

# Make sure everything is committed
git status  # Should show "nothing to commit, working tree clean"

# If not committed:
git add .
git commit -m "WIP: before cleanup"
```

### Step 2: Give AI Agent the Prompt

Copy this text and give to Claude/AI:

```
"I need you to clean up and organize my GCS Emulator repository.

Follow the steps in AI_AGENT_PROMPT.md exactly:

Phase 1: Analyze Current Structure
Phase 2: Cleanup Branches
Phase 3: Reorganize Backend (minimal-backend/)
Phase 4: Reorganize Tests (tests/)
Phase 5: Remove Legacy Files & Clutter
Phase 6: Verify Everything Works
Phase 7: Commit Changes
Phase 8: Cleanup Branches (Final)

After each phase, show me the checklist and ask before proceeding to next phase.

Here's the prompt file:
[PASTE ENTIRE AI_AGENT_PROMPT.md HERE]

Also reference these documents:
[PASTE CLAUDE.md, DEVELOPMENT_RULES.md, CLEANUP_CHECKLIST.md]

Go ahead!"
```

### Step 3: Monitor & Approve Each Phase

The AI will:
1. **Phase 1**: Show current structure → You approve
2. **Phase 2**: Show branches to delete → You confirm which ones
3. **Phase 3**: Move backend files → You verify imports work
4. **Phase 4**: Move test files → You verify tests still run
5. **Phase 5**: Delete clutter → You confirm files to remove
6. **Phase 6**: Test everything → You check all works
7. **Phase 7**: Commit → You review message
8. **Phase 8**: Delete branches → You confirm which branches to delete

**Approval Pattern**:
- AI shows what it will do
- You say "looks good, proceed" or "wait, don't do X"
- AI executes
- AI verifies
- Moves to next phase

### Step 4: After Cleanup Completes

```bash
# Pull latest if on GitHub
git pull origin

# Verify everything
python -c "from app.main import app; print('✅ Backend OK')"
cd gcp-stimulator-ui && npm run build
cd ..
pytest tests/ --collect-only

# You're done!
echo "✅ Repo cleanup complete"
```

---

## 📋 PHASES BREAKDOWN

### Phase 1: Analyze (5 min)
**AI does**: Lists current directory structure  
**You do**: Review and confirm it matches your understanding  
**Risk**: None (read-only)

### Phase 2: Backup & Delete Branches (10 min)
**AI does**: 
- Creates backup branch
- Lists branches to delete
- Asks which ones to delete

**You do**:
- Review branches
- Confirm which are safe to delete
- Say "delete X, Y, Z" or "keep everything"

**Risk**: Low (git history protected by backup branch)

### Phase 3: Backend Reorganization (30 min)
**AI does**:
- Creates app/ subdirectories
- Moves files (main.py, database.py, etc)
- Updates imports
- Tests imports work

**You do**:
- Monitor for errors
- Confirm imports updated correctly
- Test backend starts

**Risk**: Medium (file moves, import updates needed)  
**Rollback**: `git reset --hard HEAD~1`

### Phase 4: Test Reorganization (20 min)
**AI does**:
- Creates tests/ subdirectories
- Moves gcloud wrappers
- Moves test suites
- Updates pytest config

**You do**:
- Verify test structure
- Confirm tests still run
- Check pytest finds all tests

**Risk**: Medium (import updates in tests)  
**Rollback**: `git reset --hard HEAD~1`

### Phase 5: Remove Clutter (10 min)
**AI does**:
- Deletes tests/legacy/
- Removes old .env files
- Updates .gitignore
- Removes temp files

**You do**:
- Confirm files are safe to delete
- Verify nothing important removed

**Risk**: Low (only old files)  
**Rollback**: `git reset --hard HEAD~1`

### Phase 6: Verification (10 min)
**AI does**:
- Tests backend imports
- Tests frontend builds
- Tests pytest works
- Tests git status clean

**You do**:
- Review test results
- Confirm everything passes

**Risk**: None (read-only checks)

### Phase 7: Commit (5 min)
**AI does**:
- Creates proper commit message
- Commits all changes
- Shows commit in log

**You do**:
- Review commit message
- Confirm changes look good

**Risk**: Low (can revert commit if needed)  
**Rollback**: `git reset --hard HEAD~1`

### Phase 8: Final Branch Cleanup (5 min)
**AI does**:
- Lists merged branches
- Asks which to delete
- Deletes confirmed branches

**You do**:
- Review branches
- Confirm which are safe to delete
- Final verification

**Risk**: Low (only deletes merged branches)  
**Rollback**: Branches are gone but commits still in history

---

## ⚠️ CRITICAL CHECKPOINTS

**Before starting Phase 3** (file moves):
```bash
git status  # Must be clean
git branch backup/before-cleanup-$(date +%Y-%m-%d)
```

**After Phase 3** (backend moved):
```bash
python -c "from app.main import app; print('✅ OK')" || exit 1
```

**After Phase 4** (tests moved):
```bash
pytest tests/ --collect-only -q
```

**After Phase 7** (commit):
```bash
git log --oneline | head -3  # Show new commit
git status  # Should be clean
```

---

## 🛑 IF SOMETHING GOES WRONG

**Quick rollback** (within a phase):
```bash
# Undo last commit
git reset --hard HEAD~1

# Undo all changes since last commit
git checkout -- .

# Go back to backup branch
git reset --hard backup/before-cleanup-YYYY-MM-DD
```

**Don't panic**, everything is reversible!

---

## ✅ SUCCESS LOOKS LIKE

After cleanup completes:

```bash
$ tree minimal-backend/app -L 2
minimal-backend/app
├── __init__.py
├── main.py
├── api/
│   ├── __init__.py
│   ├── compute.py
│   ├── storage.py
│   └── ...
├── services/
│   ├── __init__.py
│   ├── compute/
│   ├── storage/
│   └── ...
├── models/
│   ├── __init__.py
│   └── database.py
├── core/
│   ├── __init__.py
│   └── docker.py
└── utils/
    └── __init__.py

$ pytest tests/ --collect-only
collected 45 items  # Shows all tests found

$ python -c "from app.main import app; print('✅ Backend OK')"
✅ Backend OK

$ git log --oneline | head -3
abc1234 refactor: reorganize repository structure and cleanup
def5678 WIP: before cleanup
ghi9012 Previous commit
```

---

## 📊 DECISION TREE

```
Start Cleanup
    ↓
[Phase 1] Analyze Structure
    ↓ (looks good?)
    └─→ NO → "Stop, fix manually first"
    └─→ YES ↓
[Phase 2] Backup & Delete Branches
    ↓ (branches identified?)
    └─→ NO → "Keep all branches"
    └─→ YES ↓
[Phase 3] Reorganize Backend
    ↓ (imports work?)
    └─→ NO → "Rollback, check imports"
    └─→ YES ↓
[Phase 4] Reorganize Tests
    ↓ (tests found?)
    └─→ NO → "Rollback, check pytest config"
    └─→ YES ↓
[Phase 5] Remove Clutter
    ↓ (safe to delete?)
    └─→ NO → "Skip deletions"
    └─→ YES ↓
[Phase 6] Verify Everything
    ↓ (all checks pass?)
    └─→ NO → "Rollback, fix issues"
    └─→ YES ↓
[Phase 7] Commit
    ↓ (message looks good?)
    └─→ NO → "Amend commit"
    └─→ YES ↓
[Phase 8] Final Branch Cleanup
    ↓ (ready to push?)
    └─→ NO → "Keep branches, fix later"
    └─→ YES ↓
✅ DONE! Repo is clean and organized
```

---

## 📚 REFERENCE DOCUMENTS

Before starting, make sure you have:

- ✅ **AI_AGENT_PROMPT.md** (the main prompt to give AI)
- ✅ **CLAUDE.md** (project context)
- ✅ **DEVELOPMENT_RULES.md** (for reference)
- ✅ **CLEANUP_CHECKLIST.md** (detailed steps)
- ✅ This file (QUICK_START.md)

All in your repo or ready to paste.

---

## 🎯 TIMELINE

| Phase | Time | What Happens |
|-------|------|--------------|
| 1 | 5 min | AI analyzes structure |
| 2 | 10 min | Branch cleanup |
| 3 | 30 min | Backend reorganization |
| 4 | 20 min | Test reorganization |
| 5 | 10 min | Remove clutter |
| 6 | 10 min | Verification |
| 7 | 5 min | Commit |
| 8 | 5 min | Final branch cleanup |
| **Total** | **95 min** | **~1.5 hours** |

**Actual time may vary** (plus time for your approvals between phases)

---

## 🚀 GO!

When ready:

1. ✅ Commit all pending changes
2. ✅ Copy AI_AGENT_PROMPT.md
3. ✅ Give prompt to Claude with CLAUDE.md + DEVELOPMENT_RULES.md + CLEANUP_CHECKLIST.md
4. ✅ Monitor each phase
5. ✅ Approve before proceeding
6. ✅ Celebrate clean repo! 🎉

---

**Questions?** Reference AI_AGENT_PROMPT.md or CLEANUP_CHECKLIST.md

**Ready?** Let's go! 🚀
