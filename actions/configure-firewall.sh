#!/bin/bash

# Create logs directory if it doesn't exist
BASE_PATH=$(eval echo ~$SUDO_USER)
mkdir -p "$BASE_PATH/logs"
LOG_FILE="$BASE_PATH/logs/configure-firewall.log"

log() {
    echo "[$(date)] $1" | tee -a "$LOG_FILE"
}

log "🛡️ Starting UFW firewall configuration..."

# Check if we're running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   log "❌ This script must be run with sudo or as root"
   exit 1
fi

log "📊 Current Firewall Settings:"
echo "----------------------------------"
ufw status verbose
echo "----------------------------------"

# Backup current UFW rules
ufw_backup="$BASE_PATH/logs/ufw_backup_$(date +%F_%H-%M-%S).rules"
ufw show user > "$ufw_backup" 2>/dev/null || log "⚠️ Could not backup current UFW rules"
log "✅ Current UFW configuration backed up to $ufw_backup"

# Reset UFW to ensure clean configuration
ufw --force reset
log "✅ UFW rules reset"

# Set default policies
ufw default deny incoming
ufw default allow outgoing
log "✅ Default policies set: deny incoming, allow outgoing"

# Allow SSH on the new port first (before blocking standard SSH)
ufw allow 2224/tcp && log "✅ Allowed SSH on port 2224" || log "❌ Failed to allow SSH on port 2224"

# Warn about SSH port change
log "⚠️ WARNING: This script is changing SSH from port 22 to 2224"
log "⚠️ Ensure you can connect on port 2224 before disconnecting"

# Open wide range of ports as specified in original script
ufw allow 8000:10000/udp && log "✅ Allowed UDP range 8000-10000"
ufw allow 8000:10000/tcp && log "✅ Allowed TCP range 8000-10000"

# Explicitly deny SSH on default port as requested
ufw deny 22/tcp && log "✅ Denied SSH access on default port 22/tcp"

# Enable UFW
ufw --force enable && log "✅ UFW enabled successfully" || log "❌ Failed to enable UFW!"

# Sleep to ensure UFW has updated
sleep 2

# Display current firewall status
log "📊 Updated Firewall Settings:"
echo "----------------------------------"
ufw status verbose
echo "----------------------------------"
log "🛡️ Firewall configuration completed"

# Save the final configuration to the log file
log "📊 Detailed Firewall Rules:"
echo "----------------------------------" >> "$LOG_FILE"
ufw show added >> "$LOG_FILE"
echo "----------------------------------" >> "$LOG_FILE"