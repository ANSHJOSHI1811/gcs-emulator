# 🔄 Context Window Management System

This system helps maintain continuity across chat sessions by automatically generating context checkpoints when your context window fills up.

## 📋 Overview

When working on large projects with ChatGPT/Claude, you hit context window limits. This system:

1. **Tracks your work** - Monitors files, status, and progress
2. **Generates summaries** - Creates checkpoints at strategic points
3. **Enables handoff** - Paste summary into new chat to continue seamlessly
4. **Prevents context loss** - Never lose progress due to window limits

## 🚀 Quick Start

### Generate a checkpoint (3 levels available)

```bash
# Quick summary (~500 words) - Good for quick reference
python generate_context.py --level quick

# Standard summary (~2000 words) - Recommended for handoff [DEFAULT]
python generate_context.py --level standard

# Detailed summary (~4000 words) - Full reference with code locations
python generate_context.py --level detailed
```

### Save to custom location

```bash
python generate_context.py --level standard --output /tmp/my_checkpoint.md
```

### Output

All checkpoints are saved to:
- **Primary checkpoint**: `/home/ubuntu/gcs-stimulator/CONTEXT_CHECKPOINT.md`
- **Timestamped backups**: `/home/ubuntu/gcs-stimulator/.checkpoints/checkpoint_*.md`

## 👥 Workflow: Context Handoff Between Sessions

### When your context window is ~80% full:

1. **Generate checkpoint**
   ```bash
   python generate_context.py --level standard
   ```

2. **See output**
   ```
   ✅ Checkpoint generated successfully!
   📊 Size: 2,847 bytes
   📄 Files:
      Primary: /home/ubuntu/gcs-stimulator/CONTEXT_CHECKPOINT.md
   ```

3. **Copy the file contents**
   ```bash
   cat /home/ubuntu/gcs-stimulator/CONTEXT_CHECKPOINT.md
   ```

4. **In new chat session:**
   - Paste the checkpoint at the beginning
   - Add: "Previous context loaded. Ready to continue work."
   - Start new tasks immediately

5. **Continue without losing progress**
   - New AI has full context of previous work
   - Knows what was done, current status, next steps
   - Can reference specific code locations

## 📊 Checkpoint Contents

Each checkpoint includes:

### Quick Level (~500 words)
- Current status at a glance
- Project metrics (services, components, tests)
- Current focus areas
- Key resources

### Standard Level (~2000 words) - **Recommended**
- System status (backend, frontend, testing)
- Session work summary
- Code organization reference
- File changes
- Next session priorities
- Important context reminders
- Command reference

### Detailed Level (~4000 words)
- Everything in Standard PLUS
- Full code locations with line numbers
- Implementation recommendations by phase
- Repository state details
- Known issues with workarounds
- Session statistics

## 🎯 When to Generate Checkpoints

### Automatic signals
- Before context window reaches 80% capacity (~160k tokens used)
- After completing major milestones
- Before switching to a new major task
- At end of long session

### Manual checkpoints
```bash
# Save checkpoint at any time
python generate_context.py

# Make timestamped backup
python generate_context.py --backup-only

# Keep multiple references
python generate_context.py --output backup_js_consolidation.md
python generate_context.py --output backup_autoscaling.md
```

## 💾 Checkpoint Storage

```
/home/ubuntu/gcs-stimulator/
├── CONTEXT_CHECKPOINT.md              (always current, overwritten)
└── .checkpoints/
    ├── checkpoint_quick_20260226_143022.md
    ├── checkpoint_standard_20260226_143102.md
    ├── checkpoint_detailed_20260226_143142.md
    └── [auto-saved timestamped versions]
```

## 📝 Pasting Context into New Chat

### Template for new chat:

```
[PASTE ENTIRE CONTEXT_CHECKPOINT.md HERE]

---

## Continuing from Previous Session

Previous work completed:
- [List main accomplishments from checkpoint]

Current status:
- Backend: 11/26 services implemented
- Frontend: JavaScript consolidation planned
- Cloud Run: 95% complete, verified
- Auto-Scaling: 85% complete, verified

Ready to continue with:
[Your next task]

[Reference code locations from checkpoint as needed]
```

### Example:

```
# Previous Context Checkpoint
**Generated:** February 26, 2026 - 14:30 UTC
...
[FULL CHECKPOINT CONTENT]

---

## Continuing Work

Previous session verified Cloud Run and Auto-Scaling implementations.
Now focusing on JavaScript code consolidation Phase 1.

Task: Consolidate formatBytes utility functions across 3 files.
Files involved:
- src/utils/formatBytes.ts
- src/utils/formatters.ts  
- src/components/UploadObjectModal.tsx

Starting with analysis...
```

## 🔍 Monitoring Context Window Usage

### Estimate current usage:

```python
# Rough estimate (tokens ≈ words × 1.3)
Initial system prompt:        ~500 words
Your queries:                 ~1000 words  
Responses:                    ~5000 words
Total per session:            ~6500 words
In tokens:                    ~8500 tokens

Context window limits:
- Claude 3 Opus:             200,000 tokens (~150k words)
- Claude 3 Sonnet:           200,000 tokens (~150k words)
- GPT-4:                     8,000-32,000 tokens (varies)
- GPT-4 Turbo:               128,000 tokens (~100k words)

Safe checkpoint point:        80% of limit
```

### At 80% capacity

- **Claude 3 (200k)**: ~160k tokens remaining = checkpoint time
- **GPT-4 Turbo (128k)**: ~102k tokens remaining = checkpoint time
- **GPT-4 (8k)**: ~6.4k tokens remaining = checkpoint time

## 🛠️ Advanced Usage

### Generate quick backup before risky changes

```bash
python generate_context.py --level quick --backup-only
# Saves timestamped copy without overwriting primary
```

### Create task-specific checkpoints

```bash
# Before implementing Secret Manager
python generate_context.py --output CHECKPOINT_SECRET_MANAGER.md

# Before implementing Cloud KMS
python generate_context.py --output CHECKPOINT_CLOUD_KMS.md

# Easy reference if reverting to previous task
```

### Review what changed in a session

```bash
# Compare checkpoints
diff .checkpoints/checkpoint_standard_20260226_143102.md \
     .checkpoints/checkpoint_standard_20260226_160045.md

# See progress made
```

## ⚡ Integration with Your Workflow

### Typical Session Flow:

```
1. Start Chat
   ↓
2. Paste previous checkpoint (if continuing)
   ↓
3. Work on tasks for 1-2 hours
   ↓
4. Context window reaches 80%
   ↓
5. Run: python generate_context.py
   ↓
6. Copy checkpoint to clipboard
   ↓
7. Start New Chat
   ↓
8. Paste checkpoint at top
   ↓
9. Continue work seamlessly
```

## 📊 Checkpoint Statistics

Each generated checkpoint includes:

- **Backend Status**: Routers, services, models, tests
- **Frontend Status**: Components, pages, dependencies, bundle size
- **Git Status**: Modified, added, deleted, untracked files
- **Code Locations**: Exact file paths with line numbers
- **Recommendations**: Next priorities and implementation path
- **Known Issues**: What to watch out for
- **Commands**: Quick reference for common tasks

## 🎓 Example Checkpoints in This Project

Already created:
- `CONTEXT_CHECKPOINT.md` - Current standard checkpoint
- `IMPLEMENTATION_TRACKER.md` - Service-level progress
- `ProjectContext.md` - Long-term architectural reference

You can create additional ones:
- `CHECKPOINT_JS_REFACTORING.md` - For JavaScript work
- `CHECKPOINT_CLOUD_RUN_FIX.md` - For Cloud Run issues
- `CHECKPOINT_SERVICE_X.md` - For each service implementation

## 🚨 Important Notes

1. **Always backup before major refactoring**
   ```bash
   python generate_context.py --level detailed --backup-only
   ```

2. **Keep primary checkpoint in source control**
   ```bash
   git add CONTEXT_CHECKPOINT.md
   git commit -m "context: checkpoint before [major work]"
   ```

3. **Timestamped backups let you revert**
   - Checkpoints are in `.checkpoints/` with timestamps
   - Easy to find checkpoint from specific time
   - Useful if you need to review what was done

4. **Combine with IMPLEMENTATION_TRACKER.md**
   - IMPLEMENTATION_TRACKER.md: What services are done
   - CONTEXT_CHECKPOINT.md: What you're currently working on
   - Together they form complete project memory

## 📞 Quick Reference

```bash
# Generate quick checkpoint (for frequent handoffs)
python generate_context.py --level quick

# Generate full checkpoint (best for detailed work)
python generate_context.py --level standard

# Generate detailed checkpoint (for complex issues)
python generate_context.py --level detailed

# Save timestamped backup without overwriting
python generate_context.py --backup-only

# Save to custom file for reference
python generate_context.py --output my_checkpoint.md

# View current checkpoint
cat /home/ubuntu/gcs-stimulator/CONTEXT_CHECKPOINT.md

# See all checkpoints
ls -la /home/ubuntu/gcs-stimulator/.checkpoints/

# Compare two checkpoints
diff checkpoint1.md checkpoint2.md
```

## ✅ Setup Complete!

You now have a complete context management system:

1. ✅ **CONTEXT_CHECKPOINT.md** - Always-current checkpoint
2. ✅ **generate_context.py** - Automated checkpoint generator
3. ✅ **This README** - Usage instructions
4. ✅ **Timestamped backups** - Automatic archival

**Ready to use**: Next time context window fills, run `python generate_context.py` and seamlessly continue in new chat! 🚀

---

**Created:** February 26, 2026  
**Project:** GCS Stimulator Development  
**Purpose:** Maintain continuity across context windows
