#!/bin/bash
# update-firedancer.sh
# Updates the Firedancer checkout to a specified git ref (normally a release
# tag) and installs its dependencies (deps.sh). The actual build is done
# separately by make-firedancer.sh.
#
# Usage: ./update-firedancer.sh <git-ref>
#
# Works whether run directly as the validator user or via sudo. When invoked
# via sudo it re-execs as the original user so the checkout and dependency
# files are owned by that user (not root), keeping a later non-sudo build and
# `git` operations working.
#
# Exit codes propagate to the caller: any failure aborts and returns non-zero.

set -euo pipefail

# Resolve our own absolute path before anything else so the re-exec below is
# robust regardless of the caller's cwd.
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

# If invoked as root via sudo, drop back to the invoking user so git and
# deps.sh do not leave root-owned files under the user's home.
if [ "$(id -u)" -eq 0 ] && [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
    exec sudo -u "$SUDO_USER" -H bash "$SCRIPT_PATH" "$@"
fi

# Shared base-path resolution and log() helper.
# shellcheck source=lib/firedancer-common.sh
source "$SCRIPT_DIR/lib/firedancer-common.sh"

# Accept the ref as a command-line argument (empty if omitted; no set -u blow-up)
REF="${1:-}"

BASE_PATH="$(resolve_base_path)"
LOG_DIR="$BASE_PATH/logs"
LOG_FILE="$LOG_DIR/firedancer-update.log"
REPO_DIR="$BASE_PATH/code/firedancer"

# Ensure the logging directory exists before we try to write to it.
mkdir -p "$LOG_DIR" || { echo "❌ ERROR: Could not create log directory $LOG_DIR"; exit 1; }

# Validate input.
if [ -z "$REF" ]; then
    log "❌ ERROR: No git ref provided. Usage: $0 <git-ref>"
    exit 1
fi

log "🔥 Updating Firedancer to ref: $REF"
log "📁 Base path: $BASE_PATH"
log "📁 Repository: $REPO_DIR"

# Navigate to the repo and confirm it is a git working tree.
cd "$REPO_DIR" || { log "❌ ERROR: Failed to change directory to $REPO_DIR"; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || { log "❌ ERROR: $REPO_DIR is not a git repository"; exit 1; }

# Refuse to switch refs over uncommitted changes: a detached checkout would
# otherwise abort with a cryptic git error (or clobber work). Submodule state
# is ignored here — `git submodule update` below reconciles it. Fail loudly
# instead of letting set -e kill the script with no explanation.
if ! git diff --quiet --ignore-submodules || ! git diff --cached --quiet --ignore-submodules; then
    log "❌ ERROR: working tree has uncommitted changes; commit or stash them before updating"
    exit 1
fi

# Fetch the latest refs and tags from origin only. (--all would contact every
# configured remote and abort the whole update if an unrelated extra remote is
# unreachable or auth-gated.)
log "📥 Fetching latest refs and tags from origin..."
git fetch --tags origin 2>&1 | tee -a "$LOG_FILE"

# Validate the ref resolves to a commit. `^{commit}` accepts tags, branches,
# and raw SHAs, preserving the previous script's acceptance of any commit-ish.
if ! git rev-parse -q --verify "${REF}^{commit}" >/dev/null 2>&1; then
    log "❌ ERROR: ref '$REF' not found in repository after fetch"
    exit 1
fi

# Check out the ref in detached HEAD: avoids polluting the branch namespace and
# the tag/branch name-collision ambiguity that a local branch named after a tag
# would create on repeated runs.
log "🌿 Checking out ref: $REF"
git checkout --detach "$REF" 2>&1 | tee -a "$LOG_FILE"

log "✅ Now at: $(git describe --tags --always)"

log "🔁 Updating submodules..."
git submodule update --init --recursive 2>&1 | tee -a "$LOG_FILE"
log "✅ Submodules updated"

# Run deps.sh attached to the terminal (NOT piped through tee) so its manual
# approval prompt stays visible and interactive, as the README flow requires.
log "📦 Installing dependencies (deps.sh) — approve the prompt if asked..."
if ! ./deps.sh; then
    log "❌ ERROR: deps.sh failed"
    exit 1
fi
log "✅ deps.sh ran successfully"

log "🎉 Update complete. Run make-firedancer.sh to build."
