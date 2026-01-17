#!/bin/bash
# update-firedancer.sh
# This script updates Firedancer to a specified git tag
# Works both when run via sudo and when run directly as a user

# Set variables
TAG="$1"  # Accepts tag as a command-line argument

# Determine the correct base path
# Priority: $SUDO_USER home > $USER home > $HOME
if [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
    # Running via sudo - use the original user's home
    BASE_PATH=$(eval echo ~$SUDO_USER)
elif [ -n "$USER" ] && [ "$USER" != "root" ]; then
    # Running as non-root user directly
    BASE_PATH=$(eval echo ~$USER)
else
    # Fallback to $HOME
    BASE_PATH="$HOME"
fi

LOG_FILE="$BASE_PATH/logs/firedancer-update.log"
REPO_DIR="$BASE_PATH/code/firedancer"

# Ensure logging directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Start logging
{
    if [ -z "$TAG" ]; then
        echo "❌ ERROR: No tag provided."
        exit 1
    else
        echo "[$(date)] 🔥 Updating Firedancer to tag: $TAG"
        echo "📁 Base path: $BASE_PATH"
        echo "📁 Repository: $REPO_DIR"
    fi

    # Navigate to repo
    cd "$REPO_DIR" || { echo "❌ ERROR: Failed to change directory to $REPO_DIR"; exit 1; }

    # Checkout main and fetch latest updates
    echo "🔄 Checking out main branch..."
    git checkout main

    echo "📥 Pulling latest changes..."
    git pull

    echo "🏷️ Fetching tags..."
    git fetch --tags

    echo "🌿 Preparing version: $TAG"
    # Try to create a new branch from the tag; fall back to checkout if it exists
    if git switch -c "$TAG" "$TAG" 2>/dev/null; then
        echo "🆕 Created and switched to new branch: $TAG"
    else
        git checkout "$TAG"
        echo "↪️ Switched to existing branch/tag: $TAG"
    fi

    echo "✅ Done! Now on branch: $(git branch --show-current)"

    echo "Updating Sub modules"
    git submodule update --init --recursive

    echo "✅ Done Updating Sub modules"

    echo "Install dependencies -- deps.sh"
    ./deps.sh || { echo "❌ ERROR: Failed to execute deps.sh"; exit 1; }
    echo "deps.sh ran successfully!"

    echo "[$(date)] 🎉 Update complete."
} 2>&1 | tee -a "$LOG_FILE"
