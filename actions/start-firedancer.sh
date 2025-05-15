#!/bin/bash

BASE_PATH=$(eval echo ~$SUDO_USER)
LOG_FILE="$BASE_PATH/logs/start-firedancer.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Attempt to start Frankendancer service with error handling
if sudo systemctl start frankendancer.service; then
    log_message "Successfully started Frankendancer service."
else
    log_message "Failed to start Frankendancer service."
    journalctl -u frankendancer.service -n 20 | tee -a "$LOG_FILE"
    exit 1
fi
