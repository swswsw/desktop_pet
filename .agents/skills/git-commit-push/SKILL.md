---
name: git-commit-push
description: >-
  Use this skill to automatically test, stage, commit, and push changes to the remote git repository after completing code edits or whenever the user asks to save, commit, or sync changes.
---

# Git Commit and Push Skill

Automated workflow to verify, stage, commit, and push project changes to GitHub.

## When to Use This Skill
- After completing a code modification, feature addition, or bug fix.
- Whenever the user requests to "commit and push", "save progress", or "sync changes".
- As an automated step to record working milestones.

---

## Workflow Steps

### 1. Verify Working State
Before committing, inspect modified files and ensure automated tests pass:
```bash
git status
```
If test files exist (e.g. `test_pet.py`), run them:
```bash
python3 test_pet.py
```
Do not push if tests fail.

### 2. Execute Automated Commit & Push
Run the bundled helper script with a descriptive commit message:
```bash
./.agents/skills/git-commit-push/scripts/commit_and_push.sh "<commit-message>"
```

Alternatively, run the standard git sequence:
```bash
git add .
git commit -m "<type>: <concise description of changes>"
git push origin $(git rev-parse --abbrev-ref HEAD)
```

### 3. Commit Message Conventions
Follow Conventional Commits where appropriate:
- `feat: <description>` - New features or capabilities
- `fix: <description>` - Bug fixes or behavior corrections
- `docs: <description>` - Documentation or README updates
- `refactor: <description>` - Code refactoring without changing behavior
- `test: <description>` - Adding or updating automated tests
- `chore: <description>` - Maintenance, configurations, or minor tweaks

### 4. Verification
Check that the push was successful:
```bash
git status
```
Working tree should be clean, and local branch should be up-to-date with `origin`.
