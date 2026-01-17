#!/bin/bash
# make-firedancer.sh - Build Firedancer with proper exit code handling

# Configurations
# Determine the correct base path (same logic as update-firedancer.sh)
if [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
    BASE_PATH=$(eval echo ~$SUDO_USER)
elif [ -n "$USER" ] && [ "$USER" != "root" ]; then
    BASE_PATH=$(eval echo ~$USER)
else
    BASE_PATH="$HOME"
fi

LOG_DIR="$BASE_PATH/logs"
LOG_FILE="$LOG_DIR/validator-make-reboot.log"
REPO_DIR="$BASE_PATH/code/firedancer"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function to log messages
log() {
    echo "[$(date)] $1" | tee -a "$LOG_FILE"
}

log "🚀 Starting Firedancer make and reboot process! This next step will cause the validator to go delinquent!!"
log "📁 Base path: $BASE_PATH"
log "📁 Repository: $REPO_DIR"

log "🛠️  Building fdctl and solana..."
cd "$REPO_DIR" || { log "❌ ERROR: Could not change directory to $REPO_DIR"; exit 1; }

# Start timing the make command
START_TIME=$(date +%s)
make -j fdctl solana 2>&1 | tee -a "$LOG_FILE"
MAKE_EXIT_CODE=$?  # ✅ Capture exit code IMMEDIATELY after make
# End timing the make command
END_TIME=$(date +%s)

# Calculate duration
DURATION=$((END_TIME - START_TIME))
log "⏱️  Make command took $DURATION seconds."

# Check if make command was successful using the captured exit code
if [ $MAKE_EXIT_CODE -eq 0 ]; then
    log "✅ Build completed successfully."
    exit 0
else
    log "❌ Build failed. Not rebooting."
    exit $MAKE_EXIT_CODE
fi

# separate script for stopping the validator service

# log "Stopping Validator Service"
# sudo systemctl stop frankendancer.service
# log "Validator Service Stopped "

# # Log reboot and execute it
# log "🔄 Rebooting system to apply changes..."
# echo "Rebooting at $(date)" >> "$LOG_FILE"
# sudo reboot
