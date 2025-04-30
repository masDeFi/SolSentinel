"""
This workflow configures a new validator
Assumes you just ssh'd in for the first time as root
To run: python3 workflows/configure-validator.py
Update server 
 ->summarize_package_updates.py
 ->install_package_updates.py
Create user
 ->create_user.py
Configure Security
 ->configure_fail2ban.py
 ->diable_auto_updates.py
 ->configure_ssh.py
Configure Performance
 ->configure_swap.py
 ->set-cpus-performance.sh
"""
import subprocess
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='workflow.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Steps as described in config-validator.py
steps = [
    ("Update server", [
        ("Summarize package updates", "summarize_package_updates.py"),
        ("Install package updates", "install_package_updates.py"),
    ]),
    ("Create user", [
        ("Create user", "create_user.py"),
    ]),
    ("Configure Security", [
        ("Configure fail2ban", "configure_fail2ban.py"),
        ("Disable auto updates", "diable_auto_updates.py"),
        ("Configure SSH", "configure_ssh.py"),
    ]),
    ("Configure Performance", [
        ("Configure swap", "configure_swap.py"),
        ("Set CPUs to performance mode", "set-cpus-performance.sh"),
    ]),
]


def run_script(script):
    """Run a script and log its output."""
    ext = os.path.splitext(script)[1]
    if ext == '.py':
        cmd = ['python3', script]
    elif ext == '.sh':
        cmd = ['bash', script]
    else:
        logging.warning(f"Unknown script type for {script}, skipping.")
        print(f"[SKIP] Unknown script type for {script}")
        return
    try:
        logging.info(f"Running {script}")
        print(f"[RUN] {script}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logging.info(f"Output of {script}:\n{result.stdout}")
        if result.stderr:
            logging.warning(f"Stderr of {script}:\n{result.stderr}")
        print(f"[SUCCESS] {script}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running {script}: {e}\nStdout: {e.stdout}\nStderr: {e.stderr}")
        print(f"[FAIL] {script}")

def main():
    print("Starting workflow at", datetime.now())
    for section, actions in steps:
        print(f"\n=== {section} ===")
        logging.info(f"Section: {section}")
        for desc, script in actions:
            print(f"-> {desc}")
            logging.info(f"Step: {desc} ({script})")
            run_script(script)
    print("\nWorkflow complete.")
    logging.info("Workflow complete.")

if __name__ == "__main__":
    main() 