import shutil
import re
import os
import subprocess
import argparse

# === CONFIGURATION ===
DEFAULT_SSH_PORT = 2222  # Default SSH port if none specified
CUSTOM_CONFIG_DIR = "/etc/ssh/sshd_config.d"
CUSTOM_CONFIG_FILE = f"{CUSTOM_CONFIG_DIR}/custom-sentinel-ssh.conf"
SSHD_CONFIG = "/etc/ssh/sshd_config"

# === FUNCTIONS ===
def check_include_directive():
    """Checks if the main sshd_config includes the sshd_config.d directory."""
    with open(SSHD_CONFIG, 'r') as f:
        content = f.read()
    if "Include /etc/ssh/sshd_config.d/*.conf" not in content:
        print("\n❗ 'Include /etc/ssh/sshd_config.d/*.conf' not found in sshd_config.")
        print("Adding it now...")
        with open(SSHD_CONFIG, 'a') as f:
            f.write("\nInclude /etc/ssh/sshd_config.d/*.conf\n")
        print("Include directive added to sshd_config.")
    else:
        print("Include directive already present in sshd_config.")

def create_custom_config(port):
    """Creates a custom SSH configuration file with the desired settings."""
    print("Creating custom SSH configuration...")
    config_content = f"""# Custom SSH hardening settings
PermitRootLogin no
PasswordAuthentication no
UsePAM no
Port {port}
"""
    
    os.makedirs(CUSTOM_CONFIG_DIR, exist_ok=True)

    with open(CUSTOM_CONFIG_FILE, 'w') as f:
        f.write(config_content)

    print(f"Custom config written to {CUSTOM_CONFIG_FILE}")

def validate_ssh_config():
    """Validates the SSH configuration using sshd -t."""
    print("Validating SSH configuration...")
    result = subprocess.run(["sshd", "-t"], capture_output=True)
    if result.returncode == 0:
        print("SSH configuration is valid.")
        return True
    else:
        print("SSH configuration is INVALID:")
        print(result.stderr.decode())
        return False

def restart_ssh():
    """Attempts to restart the SSH service."""
    print("Restarting SSH service...")
    try:
        subprocess.run(["systemctl", "restart", "ssh"], check=True)
    except subprocess.CalledProcessError:
        try:
            subprocess.run(["systemctl", "restart", "sshd"], check=True)
        except subprocess.CalledProcessError as e:
            print("Failed to restart SSH service. Please restart manually!")
            print(e)

# === MAIN ===
def main():
    parser = argparse.ArgumentParser(description='Configure SSH with custom hardening settings.')
    parser.add_argument('--port', type=int, default=DEFAULT_SSH_PORT,
                      help=f'SSH port number (default: {DEFAULT_SSH_PORT})')
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        print("Error: Port number must be between 1 and 65535")
        return

    if os.geteuid() != 0:
        print("This script must be run as root.")
        return

    print("\n⚠️  Important Warning: If you mess up the SSH config and restart without checking, you can lock yourself out.")
    print("It is highly recommended to test the SSH configuration with 'sshd -t' before restarting.")
    confirm = input("Do you want to proceed with creating a custom SSH config? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Aborting.")
        return

    check_include_directive()
    create_custom_config(args.port)

    if not validate_ssh_config():
        print("Fix the SSH configuration issues before restarting the SSH service.")
        return

    print("\n⚠️  IMPORTANT: You still need to restart SSH for changes to take effect.")
    confirm_restart = input("Do you want to restart SSH service now? (yes/no): ")
    if confirm_restart.lower() == 'yes':
        restart_ssh()
    else:
        print("Please remember to restart SSH manually for changes to take effect.")

if __name__ == "__main__":
    main()