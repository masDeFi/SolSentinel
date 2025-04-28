#!/usr/bin/env python3

import subprocess
import logging

# Setup logging
LOG_FILE = "disable_auto_updates.log"
logging.basicConfig(filename=LOG_FILE,
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def run_cmd(cmd, check=False):
    """Helper to run shell commands with logging."""
    logging.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout.strip():
            logging.info(f"Command output: {result.stdout.strip()}")
        if result.stderr.strip():
            logging.warning(f"Command error output: {result.stderr.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        if check:
            raise
        return e

def disable_unattended_upgrades():
    """Disable unattended-upgrades service if installed."""
    logging.info("Disabling unattended-upgrades service...")
    run_cmd(["sudo", "systemctl", "disable", "--now", "unattended-upgrades.service"], check=False)

def disable_apt_timers():
    """Disable apt-daily and apt-daily-upgrade timers."""
    timers = ["apt-daily.timer", "apt-daily-upgrade.timer"]
    for timer in timers:
        logging.info(f"Disabling {timer}...")
        run_cmd(["sudo", "systemctl", "disable", "--now", timer], check=False)

def main():
    logging.info("Starting automatic updates disabling process...")
    disable_unattended_upgrades()
    disable_apt_timers()
    logging.info("Finished disabling automatic updates.")

if __name__ == "__main__":
    main()
