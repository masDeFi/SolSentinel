#!/bin/bash
# complete_update_firedancer.sh
# Perform a complete, safety-gated Firedancer update:
#   identity check -> stop -> checkout/pull -> deps -> build -> verify
#   -> configure -> identity check -> start -> identity check -> catchup.
#
# Usage: ./complete_update_firedancer.sh <git-ref> [expected-fdctl-version]
#
# The second argument is optional for normal release tags. It is useful when a
# release's `fdctl version` output intentionally differs from its git tag.

set -euo pipefail

PRIMARY_IDENTITY="mastWEbKEMjvBCd1uaUBpNjWcfSPhXMWnH9tTrgzn1g"
SERVICE_NAME="frankendancer.service"

# Resolve our own absolute path before re-execing as the validator user.
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

# Git, deps, and build artifacts must belong to the validator user. Retain the
# optional RPC override while dropping privileges from a sudo invocation.
if [ "$(id -u)" -eq 0 ] && [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
    exec sudo -u "$SUDO_USER" -H env \
        SOLANA_RPC_URL="${SOLANA_RPC_URL:-}" \
        bash "$SCRIPT_PATH" "$@"
fi

if [ "$(id -u)" -eq 0 ]; then
    echo "ERROR: Do not run as a root login. Run as the validator user or use sudo from that user." >&2
    exit 1
fi

# shellcheck source=lib/firedancer-common.sh
# shellcheck disable=SC1091 # resolved from SCRIPT_DIR, independent of cwd
source "$SCRIPT_DIR/lib/firedancer-common.sh"

REF="${1:-}"
EXPECTED_FDCTL_VERSION="${2:-}"
BASE_PATH="$(resolve_base_path)"
LOG_DIR="$BASE_PATH/logs"
LOG_FILE="$LOG_DIR/firedancer-update.log"
REPO_DIR="$BASE_PATH/code/firedancer"
ACTIVE_IDENTITY="$BASE_PATH/active-identity.json"
FDCTL="$REPO_DIR/build/native/gcc/bin/fdctl"
SOLANA_BIN_DIR="$BASE_PATH/.local/share/solana/install/active_release/bin"
CONFIGURE_SCRIPT="${FIREDANCER_CONFIGURE_SCRIPT:-$SCRIPT_DIR/configure-firedancer.sh}"
SERVICE_STOPPED_BY_SCRIPT=false
UPDATE_COMPLETE=false

mkdir -p "$LOG_DIR" || {
    echo "ERROR: Could not create log directory $LOG_DIR" >&2
    exit 1
}

on_exit() {
    local exit_code=$?
    if [ "$exit_code" -ne 0 ] && [ "$SERVICE_STOPPED_BY_SCRIPT" = true ]; then
        log "ERROR: Update failed after the validator was stopped. $SERVICE_NAME remains stopped for safety."
    fi
    if [ "$exit_code" -ne 0 ] && [ "$UPDATE_COMPLETE" = false ]; then
        log "ERROR: Firedancer update did not complete (exit $exit_code). See $LOG_FILE."
    fi
}
trap on_exit EXIT

fail() {
    log "ERROR: $1"
    exit 1
}

find_tool() {
    local tool_name="$1"
    local installed_path="$SOLANA_BIN_DIR/$tool_name"
    if command -v "$tool_name" >/dev/null 2>&1; then
        command -v "$tool_name"
    elif [ -x "$installed_path" ]; then
        printf '%s\n' "$installed_path"
    else
        return 1
    fi
}

expected_version_for_ref() {
    case "$1" in
        v0.904.40006) printf '%s\n' "0.33672.40006" ;;
        v0.905.40007) printf '%s\n' "0.33673.40007" ;;
        v0.1004.40101) printf '%s\n' "0.1004.0-rc.40101" ;;
        v[0-9]*.[0-9]*.[0-9]*) printf '%s\n' "${1#v}" ;;
        [0-9]*.[0-9]*.[0-9]*) printf '%s\n' "$1" ;;
        *) return 1 ;;
    esac
}

read_active_identity() {
    [ -r "$ACTIVE_IDENTITY" ] || return 1
    "$SOLANA_KEYGEN" pubkey "$ACTIVE_IDENTITY" 2>/dev/null
}

assert_non_primary_identity() {
    local phase="$1"
    local active_pubkey

    if ! active_pubkey="$(read_active_identity)" || [ -z "$active_pubkey" ]; then
        log "ERROR: Cannot read the active identity during $phase: $ACTIVE_IDENTITY"
        return 1
    fi

    log "Identity safety check ($phase): $active_pubkey"
    if [ "$active_pubkey" = "$PRIMARY_IDENTITY" ]; then
        log "ERROR: Refusing to continue with primary identity $PRIMARY_IDENTITY. Transfer to the unstaked identity first."
        return 1
    fi
}

service_active_state() {
    sudo systemctl is-active "$SERVICE_NAME" 2>/dev/null || true
}

if [ -z "$REF" ]; then
    fail "No git ref provided. Usage: $0 <git-ref> [expected-fdctl-version]"
fi
case "$REF" in
    -*) fail "Git ref must not begin with '-': $REF" ;;
esac

for required_command in git make sudo systemctl tee grep head; do
    command -v "$required_command" >/dev/null 2>&1 \
        || fail "Required command not found: $required_command"
done

SOLANA_KEYGEN="$(find_tool solana-keygen)" \
    || fail "solana-keygen not found in PATH or $SOLANA_BIN_DIR"
SOLANA="$(find_tool solana)" \
    || fail "solana not found in PATH or $SOLANA_BIN_DIR"

if [ -z "$EXPECTED_FDCTL_VERSION" ]; then
    EXPECTED_FDCTL_VERSION="$(expected_version_for_ref "$REF")" \
        || fail "Cannot infer fdctl version from '$REF'; provide it as the second argument"
fi
EXPECTED_FDCTL_VERSION="${EXPECTED_FDCTL_VERSION#v}"
[ -x "$CONFIGURE_SCRIPT" ] || fail "Configure script is not executable: $CONFIGURE_SCRIPT"

[ -d "$REPO_DIR" ] || fail "Firedancer repository does not exist: $REPO_DIR"
cd "$REPO_DIR"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || fail "$REPO_DIR is not a git repository"

if ! git diff --quiet --ignore-submodules \
    || ! git diff --cached --quiet --ignore-submodules \
    || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    fail "Working tree has changes; commit, stash (including untracked files), or remove them before updating"
fi

SERVICE_WAS_RUNNING=false
# Authenticate sudo before stopping anything, so a credential problem cannot
# strand the validator unnecessarily.
sudo -v || fail "Unable to authenticate sudo"

SERVICE_STATE="$(service_active_state)"
case "$SERVICE_STATE" in
    active)
        SERVICE_WAS_RUNNING=true
        assert_non_primary_identity "pre-stop" \
            || fail "Running validator did not pass the identity safety gate; service was not stopped"
        ;;
    inactive|failed)
        ;;
    *)
        fail "Cannot safely update while $SERVICE_NAME is in state '${SERVICE_STATE:-unknown}'"
        ;;
esac

log "Starting complete Firedancer update to $REF (expected fdctl $EXPECTED_FDCTL_VERSION)"
log "Repository: $REPO_DIR"

if [ "$SERVICE_WAS_RUNNING" = true ]; then
    log "Stopping $SERVICE_NAME..."
    sudo systemctl stop "$SERVICE_NAME"
    STOPPED_STATE="$(service_active_state)"
    case "$STOPPED_STATE" in
        inactive|failed) ;;
        *) fail "$SERVICE_NAME did not stop cleanly (state: ${STOPPED_STATE:-unknown})" ;;
    esac
    SERVICE_STOPPED_BY_SCRIPT=true
    log "$SERVICE_NAME stopped"
else
    log "$SERVICE_NAME was not running; continuing with the update"
fi

log "Fetching refs and tags from origin..."
git fetch --tags origin 2>&1 | tee -a "$LOG_FILE"
git rev-parse -q --verify "${REF}^{commit}" >/dev/null 2>&1 \
    || fail "Ref '$REF' was not found after fetching origin"

log "Checking out $REF..."
git checkout --detach "$REF" 2>&1 | tee -a "$LOG_FILE"

log "Pulling $REF from origin with fast-forward-only safety..."
git pull --ff-only origin "$REF" 2>&1 | tee -a "$LOG_FILE"

HEAD_COMMIT="$(git rev-parse 'HEAD^{commit}')"
PULLED_COMMIT="$(git rev-parse 'FETCH_HEAD^{commit}')"
[ "$HEAD_COMMIT" = "$PULLED_COMMIT" ] \
    || fail "Checkout verification failed: HEAD $HEAD_COMMIT is not pulled commit $PULLED_COMMIT"
log "Source checkout verified at $HEAD_COMMIT ($(git describe --tags --always))"

log "Updating submodules..."
git submodule update --init --recursive 2>&1 | tee -a "$LOG_FILE"

log "Installing dependencies with deps.sh (approve its prompt if asked)..."
./deps.sh
log "Dependencies updated"

if [ -f "$BASE_PATH/.cargo/env" ]; then
    # shellcheck disable=SC1091 # validator-specific Rust environment
    source "$BASE_PATH/.cargo/env"
fi

log "Building fdctl and solana..."
BUILD_START="$(date +%s)"
if make -j fdctl solana 2>&1 | tee -a "$LOG_FILE"; then
    BUILD_DURATION=$(($(date +%s) - BUILD_START))
    log "Build completed successfully in ${BUILD_DURATION}s"
else
    fail "Firedancer build failed"
fi

[ -x "$FDCTL" ] || fail "Built fdctl binary not found: $FDCTL"
FDCTL_OUTPUT="$("$FDCTL" version 2>&1)" || fail "fdctl version command failed"
printf '%s\n' "$FDCTL_OUTPUT" | tee -a "$LOG_FILE"
ACTUAL_FDCTL_VERSION="$(printf '%s\n' "$FDCTL_OUTPUT" \
    | grep -Eo 'v?[0-9]+(\.[0-9]+)+(-[0-9A-Za-z.-]+)?' \
    | head -n 1 || true)"
ACTUAL_FDCTL_VERSION="${ACTUAL_FDCTL_VERSION#v}"
[ -n "$ACTUAL_FDCTL_VERSION" ] \
    || fail "Could not parse a version from fdctl output"
[ "$ACTUAL_FDCTL_VERSION" = "$EXPECTED_FDCTL_VERSION" ] \
    || fail "Version verification failed: expected $EXPECTED_FDCTL_VERSION, got $ACTUAL_FDCTL_VERSION"
log "Version verified: source $REF, fdctl $ACTUAL_FDCTL_VERSION"

log "Configuring Firedancer for the updated build..."
if SUDO_USER="$(id -un)" HOME="$BASE_PATH" "$CONFIGURE_SCRIPT"; then
    log "Firedancer configuration completed successfully"
else
    fail "configure-firedancer.sh failed"
fi

assert_non_primary_identity "pre-start" \
    || fail "Validator will not be started with the primary identity"

log "Starting $SERVICE_NAME..."
sudo systemctl start "$SERVICE_NAME"
STARTED_STATE="$(service_active_state)"
[ "$STARTED_STATE" = active ] \
    || fail "$SERVICE_NAME did not become active (state: ${STARTED_STATE:-unknown})"

# Detect a last-moment identity change. Stop immediately rather than allowing
# a primary identity to remain live on this validator.
if ! assert_non_primary_identity "post-start"; then
    log "Stopping $SERVICE_NAME immediately because the post-start identity check failed"
    sudo systemctl stop "$SERVICE_NAME" || true
    fail "Post-start identity safety check failed"
fi
SERVICE_STOPPED_BY_SCRIPT=false
log "$SERVICE_NAME is active with a non-primary identity"

log "Waiting for the validator to catch up; Solana progress follows..."
CATCHUP_ARGS=(catchup --our-localhost)
if [ -n "${SOLANA_RPC_URL:-}" ]; then
    CATCHUP_ARGS+=(--url "$SOLANA_RPC_URL")
    log "Catchup RPC: $SOLANA_RPC_URL"
fi
if "$SOLANA" "${CATCHUP_ARGS[@]}" 2>&1 | tee -a "$LOG_FILE"; then
    log "Validator is caught up"
else
    fail "Validator is running, but the catchup command failed before reporting caught up"
fi

UPDATE_COMPLETE=true
log "Complete Firedancer update finished successfully: $REF / fdctl $ACTUAL_FDCTL_VERSION"
