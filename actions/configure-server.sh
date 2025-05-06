#!/bin/bash

# Configurations
BASE_PATH=$(eval echo ~$SUDO_USER)
LOG_DIR="$BASE_PATH/logs"
LOG_FILE="$LOG_DIR/configure-server.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function to log messages
log() {
    echo "[$(date)] $1" | tee -a "$LOG_FILE"
}

log "🚀 Starting configure server setup."

# Step 1: Mount Drives
log "🗄️ Mounting drives..."
if $BASE_PATH/mount-drives.sh >> "$LOG_FILE" 2>&1; then
    log "✅ Drives mounted successfully."
else
    log "❌ ERROR: Failed to mount drives!"
    exit 1
fi

# Step 2: Set CPUs to Performance Mode
log "⚙️ Setting CPUs to performance mode..."
if ./set-cpus-performance.sh >> "$LOG_FILE" 2>&1; then
    log "✅ CPU mode set successfully."
else
    log "❌ ERROR: Failed to set CPU performance mode!"
    exit 1
fi

# Step 3: Set Swappiness to Zero
log "🔧 Adjusting swappiness..."
if sudo sysctl vm.swappiness=0 >> "$LOG_FILE" 2>&1; then
    log "✅ Swappiness set to 0."
else
    log "❌ ERROR: Failed to set swappiness!"
    exit 1
fi

# Step 4: Configure Firewall
log "🛡️ Configuring firewall..."
if sudo ./configure-firewall.sh >> "$LOG_FILE" 2>&1; then
    log "✅ Firewall configured successfully."
else
    log "❌ ERROR: Failed to configure firewall!"
    exit 1
fi

log "🎉 Post-reboot setup complete!"
