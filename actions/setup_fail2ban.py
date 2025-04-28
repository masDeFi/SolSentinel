#!/usr/bin/env python3

import subprocess
import logging
import os
import sys

# Setup logging
LOG_FILE = "fail2ban_setup.log"
logging.basicConfig(filename=LOG_FILE,
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def run_cmd(cmd, check=False):
    """Helper to run shell commands with logging."""
    logging.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        logging.info(f"Command output: {result.stdout.strip()}")
        if result.stderr.strip():
            logging.warning(f"Command error output: {result.stderr.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        if check:
            sys.exit(1)
        return e

def check_fail2ban_installed():
    """Check if fail2ban is installed."""
    result = run_cmd(["which", "fail2ban-client"])
    return result.returncode == 0

def install_fail2ban():
    """Install fail2ban using apt."""
    logging.info("Installing fail2ban...")
    run_cmd(["sudo", "apt-get", "update"], check=True)
    run_cmd(["sudo", "apt-get", "install", "-y", "fail2ban"], check=True)
    logging.info("fail2ban installation complete.")

def ensure_service_running(service="fail2ban"):
    """Ensure the fail2ban service is active and enabled."""
    # Check status
    status = run_cmd(["systemctl", "is-active", service])
    if status.returncode != 0:
        logging.info(f"{service} service is not running. Attempting to start...")
        run_cmd(["sudo", "systemctl", "start", service], check=True)
    else:
        logging.info(f"{service} service is already running.")

    # Check enabled on boot
    enabled = run_cmd(["systemctl", "is-enabled", service])
    if enabled.returncode != 0:
        logging.info(f"{service} service is not enabled on boot. Enabling...")
        run_cmd(["sudo", "systemctl", "enable", service], check=True)
    else:
        logging.info(f"{service} service is already enabled at boot.")

def check_fail2ban_config():
    """Check fail2ban configuration sanity."""
    logging.info("Checking fail2ban configuration...")
    result = run_cmd(["sudo", "fail2ban-client", "ping"])
    if "pong" not in result.stdout.lower():
        logging.warning("fail2ban-client ping failed. Configuration may not be OK.")
    else:
        logging.info("fail2ban-client ping successful.")

def main():
    print("Starting Fail2ban validation...")
    logging.info("Starting Fail2ban setup process...")

    if not check_fail2ban_installed():
        print("fail2ban is not installed. Installing...")
        install_fail2ban()
    else:
        print("fail2ban is already installed.")

    ensure_service_running()
    check_fail2ban_config()

    print(f"Fail2ban check complete. Full log at {os.path.abspath(LOG_FILE)}")
    logging.info("Fail2ban setup process completed.")

if __name__ == "__main__":
    main()
