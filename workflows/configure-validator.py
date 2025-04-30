"""
This workflow configures a new validator
To Run
#Assumes you just ssh'd in for the first time as root
git clone https://github.com/masDeFi/SolSentinel.git
apt install python3-pip
pip install psutil
cd SolSentinel
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
import argparse

# Configure logging
logging.basicConfig(
    filename='workflow.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Steps as described in config-validator.py
steps = [
    ("Update server", [
        ("Summarize package updates", "./actions/summarize_package_updates.py"),
        ("Install package updates", "./actions/install_package_updates.py"),
    ]),
    ("Create user", [
        ("Create user", "./actions/create_user.py"),
    ]),
    ("Configure Security", [
        ("Configure fail2ban", "./actions/configure_fail2ban.py"),
        ("Disable auto updates", "./actions/disable_auto_updates.py"),
        ("Configure SSH", "../actions/configure_ssh.py"),
    ]),
    ("Configure Performance", [
        ("Configure swap", "./actions/configure_swap.py"),
        ("Set CPUs to performance mode", "./actions/set-cpus-performance.sh"),
    ]),
]

def run_script(script, extra_args=None):
    """Run a script and log its output. Returns True if success, False if fail."""
    ext = os.path.splitext(script)[1]
    if ext == '.py':
        cmd = ['python3', script]
        if extra_args:
            cmd.extend(extra_args)
    elif ext == '.sh':
        cmd = ['bash', script]
    else:
        logging.warning(f"Unknown script type for {script}, skipping.")
        print(f"[SKIP] Unknown script type for {script}")
        return True  # Not a failure, just skipped
    try:
        logging.info(f"Running {script}")
        print(f"[RUN] {script}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logging.info(f"Output of {script}:\n{result.stdout}")
        if result.stderr:
            logging.warning(f"Stderr of {script}:\n{result.stderr}")
        print(f"[SUCCESS] {script}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running {script}: {e}\nStdout: {e.stdout}\nStderr: {e.stderr}")
        print(f"[FAIL] {script}")
        if e.stdout:
            print(f"[STDOUT] {e.stdout}")
        if e.stderr:
            print(f"[STDERR] {e.stderr}")
        return False

def main(userName, set_password):
    print("Starting workflow at", datetime.now())
    total_scripts = sum(len(actions) for _, actions in steps)
    current_script = 1

    for section, actions in steps:
        print(f"\n=== {section} ===")
        logging.info(f"Section: {section}")
        for desc, script in actions:
            print(f"[{current_script}/{total_scripts}] -> {desc}")
            logging.info(f"Step: {desc} ({script})")
            extra_args = None
            # Only add userName and --set-password for create_user.py
            if script.endswith("create_user.py"):
                extra_args = [userName]
                if set_password:
                    extra_args.append("--set-password")
            success = run_script(script, extra_args=extra_args)
            if not success:
                print(f"\n[ERROR] Step '{desc}' failed. Stopping workflow.")
                logging.error(f"Workflow stopped due to failure in step: {desc}")
                return
            current_script += 1
    print("\nWorkflow complete.")
    logging.info("Workflow complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configure a new validator workflow.")
    parser.add_argument("userName", help="Username for the new user (required for create_user step)")
    parser.add_argument("--set-password", action="store_true", help="Prompt to set password for the new user interactively")
    args = parser.parse_args()
    main(args.userName, args.set_password) 