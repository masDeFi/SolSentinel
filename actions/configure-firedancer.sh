#!/bin/bash
BASE_PATH=$(eval echo ~$SUDO_USER)
LOG_FILE="$BASE_PATH/logs/configure-firedancer.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Attempt to configure Frankendancer with error handling
cd "$BASE_PATH/code/firedancer"
if sudo ./build/native/gcc/bin/fdctl configure init all --config $HOME/active-fd-config.toml; then
    log_message "Successfully configured Firedancer."
else
    log_message "Failed to configure Firedancer."
    exit 1
fi
