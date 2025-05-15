#!/bin/bash

# Configurations
BASE_PATH=$(eval echo ~$SUDO_USER)
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

log "🛠️ Building fdctl and solana..."
cd "$REPO_DIR" || { log "❌ ERROR: Could not change directory to $REPO_DIR"; exit 1; }

# Start timing the make command
START_TIME=$(date +%s)
make -j fdctl solana 2>&1 | tee -a "$LOG_FILE"
# End timing the make command
END_TIME=$(date +%s)

# Calculate duration
DURATION=$((END_TIME - START_TIME))
log "⏱️ Make command took $DURATION seconds."

# Check if make command was successful
if [ $? -eq 0 ]; then
    log "✅ Build completed successfully."
else
    log "❌ Build failed. Not rebooting."
fi

# separate script for stopping the validator service

# log "Stopping Validator Service"
# sudo systemctl stop frankendancer.service
# log "Validator Service Stopped "

# # Log reboot and execute it
# log "🔄 Rebooting system to apply changes..."
# echo "Rebooting at $(date)" >> "$LOG_FILE"
# sudo reboot
