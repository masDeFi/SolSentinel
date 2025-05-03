#!/bin/bash

# update-firedancer.sh

# This script updates the Firedancer software to a specified tag.
# It accepts a tag as a command-line argument, checks out the main branch,
# fetches the latest updates, checks out the specified tag, creates a new branch,
# and installs dependencies using deps.sh. 
# All actions are logged to a specified log file.

# Set variables
TAG="$1"  # Accepts tag as a command-line argument

BASE_PATH=$(eval echo ~$SUDO_USER)
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

    echo "🔄 Checking out tag: $TAG..."
    git checkout "$TAG"

    echo "🌿 Creating new branch: $TAG"
    git switch -c "$TAG"

    echo "✅ Done! Now on branch: $(git branch --show-current)"

    echo "Updating Sub modules"
    git submodule update

    echo "✅ Done Updating Sub modules"

    echo "Install dependencies -- deps.sh"
    ./deps.sh || { echo "❌ ERROR: Failed to execute deps.sh"; exit 1; }
    echo "deps.sh ran successfully!"

    echo "[$(date)] 🎉 Update complete."
} | tee -a "$LOG_FILE"
