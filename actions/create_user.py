import subprocess
import sys
import os

# Utility function to run shell commands with verbose logging
def run_command(command, verbose=True, shell=True):
    if verbose:
        print(f"\nRunning command: {command}")
    try:
        subprocess.run(command, check=True, shell=shell)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {command}\nError: {e}")
        sys.exit(1)

# Function to check if user already exists
def user_exists(username):
    try:
        subprocess.run(["id", username], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

# Function to create a new user
def create_user(new_user, set_password=False):
    print(f"\n➡️  Starting user creation process for: {new_user}")

    if user_exists(new_user):
        print(f"❌ User '{new_user}' already exists. Aborting.")
        sys.exit(1)

    # Option 1: Create user without a password (default, faster for setup automation)
    cmd_create_user = f"sudo adduser --disabled-password --gecos \"\" {new_user}"
    run_command(cmd_create_user)

    # Add user to sudo group for administrative privileges
    cmd_add_sudo = f"sudo usermod -aG sudo {new_user}"
    run_command(cmd_add_sudo)

    # Setup SSH folder structure under the new user's home directory
    ssh_dir = f"/home/{new_user}/.ssh"
    authorized_keys_file = os.path.join(ssh_dir, "authorized_keys")

    print("\n➡️  Setting up SSH directory and authorized_keys")
    run_command(f"sudo mkdir -p {ssh_dir}")
    run_command(f"sudo touch {authorized_keys_file}")
    run_command(f"sudo chown -R {new_user}:{new_user} {ssh_dir}")
    run_command(f"sudo chmod 700 {ssh_dir}")
    run_command(f"sudo chmod 600 {authorized_keys_file}")

    if set_password:
        # If user requested, set a password interactively
        print("\n➡️  Setting password for user")
        run_command(f"sudo passwd {new_user}")
    else:
        print("\n⚡ Skipping password setup. You can set it later with 'sudo passwd {new_user}'")

    # Create a bin directory for the user (common practice for personal scripts)
    user_bin_dir = f"/home/{new_user}/bin"
    print("\n➡️  Creating ~/bin directory")
    run_command(f"sudo mkdir -p {user_bin_dir}")
    run_command(f"sudo chown {new_user}:{new_user} {user_bin_dir}")

    print(f"\n✅ User {new_user} created and configured successfully!")

# Entry point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 create_user.py <new_user> [--set-password]")
        sys.exit(1)

    new_user = sys.argv[1]
    set_password_flag = '--set-password' in sys.argv

    create_user(new_user, set_password=set_password_flag)
