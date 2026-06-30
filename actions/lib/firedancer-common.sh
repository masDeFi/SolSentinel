#!/bin/bash
# firedancer-common.sh — shared helpers for the Firedancer management scripts.
# Source this file; it intentionally does NOT set shell options (callers own
# their own `set -e`/`pipefail`).

# resolve_base_path — echo the home directory of the operating user.
# Honors sudo via $SUDO_USER, then $USER, then $HOME. Never aborts on a missing
# passwd entry, so it is safe to call under `set -euo pipefail`: a failed
# lookup degrades to $HOME instead of killing the script.
resolve_base_path() {
    local base=""
    if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
        base=$(getent passwd "$SUDO_USER" | cut -d: -f6) || base=""
    elif [ -n "${USER:-}" ] && [ "$USER" != "root" ]; then
        base=$(getent passwd "$USER" | cut -d: -f6) || base=""
    fi
    [ -n "$base" ] || base="$HOME"
    printf '%s\n' "$base"
}

# log <message> — timestamped line to stdout and $LOG_FILE (best-effort).
# A failed log write (full disk, root-owned file) must never abort the caller,
# so the tee failure is swallowed.
log() {
    echo "[$(date)] $1" | tee -a "$LOG_FILE" 2>/dev/null || true
}
