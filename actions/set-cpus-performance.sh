#!/bin/bash
set -e

BASE_PATH=$(eval echo ~$SUDO_USER)
LOGFILE="$BASE_PATH/logs/set-cpu-performance.log"

mkdir -p "$(dirname "$LOGFILE")"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOGFILE"
}

# Check if cpufreq directory exists
if [ ! -d /sys/devices/system/cpu/cpu0/cpufreq ]; then
    log_message "❌ CPU frequency scaling not supported on this system."
    exit 1
fi

# Display available governors
log_message "Available CPU governors:"
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_available_governors | sort -u | tee -a "$LOGFILE"

log_message "Setting all CPUs to 'performance' mode..."
error_count=0

for cpu_governor in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    if echo performance > "$cpu_governor"; then
        log_message "✅ Set $(basename $(dirname "$cpu_governor")) to performance."
    else
        log_message "❌ Failed to set $(basename $(dirname "$cpu_governor")). Permission denied?"
        ((error_count++))
    fi
done

if [ "$error_count" -ne 0 ]; then
    log_message "❌ Failed to set some CPUs to performance mode. Exiting with error."
    exit 1
fi

log_message "✅ All CPU governors updated successfully!"
