#!/usr/bin/env bash
set -euo pipefail

# verify-and-pr.sh
# Verify a local branch has unique commits vs main; if none, delete it.
# If it has unique commits, push it and open a PR (using gh if available).
# Usage: verify-and-pr.sh <branch-name>

BRANCH=${1:-}
if [[ -z "${BRANCH}" ]]; then
  echo "Usage: $(basename "$0") <branch-name>" >&2
  exit 2
fi

echo "[info] Syncing refs..."
git fetch --prune

if ! git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
  echo "[warn] Local branch '${BRANCH}' not found. Aborting." >&2
  exit 1
fi

echo "[info] Ensuring main is up-to-date..."
git checkout -q main
git pull --ff-only

echo "[info] Comparing main...${BRANCH}"
COUNT_OUTPUT=$(git rev-list --left-right --count main..."${BRANCH}")
MAIN_UNIQ=$(echo "$COUNT_OUTPUT" | awk '{print $1}')
BR_UNIQ=$(echo "$COUNT_OUTPUT" | awk '{print $2}')
echo "[info] Unique commits -> main: ${MAIN_UNIQ}, ${BRANCH}: ${BR_UNIQ}"

if [[ "$BR_UNIQ" == "0" ]]; then
  echo "[info] No unique commits on '${BRANCH}'. Deleting local branch."
  git branch -D "${BRANCH}"
  # Attempt remote deletion if it exists; ignore errors
  git ls-remote --exit-code --heads origin "${BRANCH}" >/dev/null 2>&1 && \
    git push origin --delete "${BRANCH}" || true
  echo "[done] Branch '${BRANCH}' deleted (no unique commits)."
  exit 0
fi

echo "[info] Branch has ${BR_UNIQ} unique commit(s). Pushing to origin..."
git push -u origin "${BRANCH}"

if command -v gh >/dev/null 2>&1; then
  echo "[info] Creating PR with GitHub CLI..."
  gh pr create \
    --base main \
    --head "${BRANCH}" \
    --title "Merge ${BRANCH} into main" \
    --body "Automated PR created by scripts/bash/verify-and-pr.sh to track changes from '${BRANCH}'."
  echo "[done] PR created."
else
  echo "[note] 'gh' CLI not found or not authenticated. Create a PR manually on GitHub:"
  echo "       https://github.com/$(git config --get remote.origin.url | sed -E 's#.*github.com[/:]##;s#\.git$##')/compare/main...${BRANCH}?expand=1"
fi

exit 0
