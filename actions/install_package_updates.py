import subprocess
import sys
from datetime import datetime
from utils import spinner, log_and_print, LOG_FILE  # Import shared utilities
import threading
import logging
import time

# Configure logging for this script 
LOG_FILE = "package_update.log"
def log(message, level='info'):
    log_and_print(message, level=level, log_file=LOG_FILE)

def run_command(command):
    """
    Runs a shell command and logs the output.
    Returns True if successful, False otherwise.
    Shows a loading spinner while the command is running.
    """
    log(f"Running command: {' '.join(command)}")
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner, args=(stop_event, f"Running: {' '.join(command)}"))
    spinner_thread.start()
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stop_event.set()
        spinner_thread.join()
        log(f"Output: {result.stdout.strip()}")
        if result.stderr:
            log(f"Stderr: {result.stderr.strip()}", level='warning')
        return True
    except subprocess.CalledProcessError as e:
        stop_event.set()
        spinner_thread.join()
        log(f"Command failed: {' '.join(command)}", level='error')
        log(f"Error output: {e.stderr.strip()}", level='error')
        return False

def update_packages():
    """
    Updates the package list and upgrades all packages on a Linux server.
    Supports apt (Debian/Ubuntu) and yum/dnf (RHEL/CentOS/Fedora).
    """
    # Detect package manager
    pkg_managers = [
        {'name': 'apt', 'update': ['sudo', 'apt', 'update'], 'upgrade': ['sudo', 'apt', 'upgrade', '-y']},
        {'name': 'dnf', 'update': ['sudo', 'dnf', 'check-update'], 'upgrade': ['sudo', 'dnf', 'upgrade', '-y']},
        {'name': 'yum', 'update': ['sudo', 'yum', 'check-update'], 'upgrade': ['sudo', 'yum', 'update', '-y']},
    ]
    for manager in pkg_managers:
        if subprocess.call(['which', manager['name']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            log(f"Detected package manager: {manager['name']}")
            # Update package list
            if not run_command(manager['update']):
                log(f"Failed to update package list with {manager['name']}", level='error')
                return False
            # Upgrade packages
            if not run_command(manager['upgrade']):
                log(f"Failed to upgrade packages with {manager['name']}", level='error')
                return False
            log(f"Package update and upgrade completed successfully using {manager['name']}.")
            return True
    log("No supported package manager found (apt, dnf, yum).", level='error')
    return False

def main():
    log("Starting package update process...")
    start_time = datetime.now()
    success = update_packages()
    end_time = datetime.now()
    duration = end_time - start_time
    if success:
        log(f"Package update completed successfully in {duration}.")
    else:
        log(f"Package update failed after {duration}.", level='error')

if __name__ == "__main__":
    main()
