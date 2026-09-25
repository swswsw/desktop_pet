#!/usr/bin/env bash
# Helper script to verify tests, stage changes, commit, and push to origin.
set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# Check if git repo exists
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Not inside a git repository." >&2
    exit 1
fi

# Check for modified or untracked changes
if git diff-index --quiet HEAD -- 2>/dev/null && [ -z "$(git status --porcelain)" ]; then
    echo "Notice: Working tree clean, no changes to commit."
    exit 0
fi

# Run test suite if present
if [ -f "test_pet.py" ]; then
    echo "==> Running automated test suite before committing..."
    python3 test_pet.py || {
        echo "Error: Automated tests failed. Aborting commit to prevent pushing broken code." >&2
        exit 1
    }
    echo "==> Tests passed successfully."
fi

# Commit message (argument or prompt)
COMMIT_MSG="${1}"
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="chore: update workspace changes"
fi

echo "==> Staging changes..."
git add .

echo "==> Creating commit: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "==> Pushing to origin/$CURRENT_BRANCH..."
git push origin "$CURRENT_BRANCH"

echo "==> Done! Successfully pushed commit to origin/$CURRENT_BRANCH."
