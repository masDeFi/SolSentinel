#!/bin/bash
# update-firedancer.sh
# This script updates the Firedancer checkout to a specified git tag and
# installs its dependencies (deps.sh). The actual build is done separately
# by make-firedancer.sh.
#
# Works both when run via sudo and when run directly as a user.
#
# Exit codes propagate to the caller: any failure aborts and returns non-zero.

set -euo pipefail

# Accept tag as a command-line argument (no `set -u` blow-up if omitted)
TAG="${1:-}"

# Determine the correct base path (same logic as make-firedancer.sh)
# Priority: $SUDO_USER home > $USER home > $HOME
if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
    # Running via sudo - use the original user's home
    BASE_PATH=$(getent passwd "$SUDO_USER" | cut -d: -f6)
elif [ -n "${USER:-}" ] && [ "$USER" != "root" ]; then
    # Running as non-root user directly
    BASE_PATH=$(getent passwd "$USER" | cut -d: -f6)
else
    # Fallback to $HOME
    BASE_PATH="$HOME"
fi

# getent can return empty for users without a passwd entry; fall back to $HOME
[ -n "$BASE_PATH" ] || BASE_PATH="$HOME"

LOG_DIR="$BASE_PATH/logs"
LOG_FILE="$LOG_DIR/firedancer-update.log"
REPO_DIR="$BASE_PATH/code/firedancer"

# Ensure logging directory exists before we try to write to it
mkdir -p "$LOG_DIR" || { echo "❌ ERROR: Could not create log directory $LOG_DIR"; exit 1; }

# Log a message to stdout and the log file
log() {
    echo "[$(date)] $1" | tee -a "$LOG_FILE"
}

# Validate input
if [ -z "$TAG" ]; then
    log "❌ ERROR: No tag provided. Usage: $0 <git-tag>"
    exit 1
fi

log "🔥 Updating Firedancer to tag: $TAG"
log "📁 Base path: $BASE_PATH"
log "📁 Repository: $REPO_DIR"

# Navigate to repo and confirm it is a git working tree
cd "$REPO_DIR" || { log "❌ ERROR: Failed to change directory to $REPO_DIR"; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || { log "❌ ERROR: $REPO_DIR is not a git repository"; exit 1; }

# Fetch latest refs and tags up front (this is what makes $TAG resolvable)
log "📥 Fetching latest refs and tags..."
git fetch --all --tags --prune 2>&1 | tee -a "$LOG_FILE"

# Validate the requested tag exists before touching the working tree
if ! git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
    log "❌ ERROR: Tag '$TAG' not found in repository after fetch"
    exit 1
fi

# Check out the tag in detached HEAD. This avoids polluting the branch
# namespace and the tag/branch name-collision ambiguity that a local
# branch named after the tag would create on repeated runs.
log "🌿 Checking out version: $TAG"
git checkout --detach "tags/$TAG" 2>&1 | tee -a "$LOG_FILE"

log "✅ Now at: $(git describe --tags --always)"

log "🔁 Updating submodules..."
git submodule update --init --recursive 2>&1 | tee -a "$LOG_FILE"
log "✅ Submodules updated"

log "📦 Installing dependencies (deps.sh)..."
./deps.sh 2>&1 | tee -a "$LOG_FILE"
log "✅ deps.sh ran successfully"

log "🎉 Update complete. Run make-firedancer.sh to build."
