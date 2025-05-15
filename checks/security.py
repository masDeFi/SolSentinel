# checks/security.py

import subprocess
import os
import shutil
import re

def check_fail2ban():
    """Check if fail2ban service is installed, enabled, and running."""
    result = {"name": "fail2ban Service Check", "status": "PASS", "message": "", "category": "Security"}
    if shutil.which("systemctl") is None:
        result["status"] = "FAIL"
        result["message"] = "systemctl not found. Not a systemd-based system."
        return result

    try:
        proc = subprocess.run(["systemctl", "list-unit-files"], capture_output=True, text=True)
        if "fail2ban" not in proc.stdout:
            result["status"] = "FAIL"
            result["message"] = "fail2ban service is not installed."
            return result

        enabled_proc = subprocess.run(["systemctl", "is-enabled", "fail2ban"], capture_output=True, text=True)
        active_proc = subprocess.run(["systemctl", "is-active", "fail2ban"], capture_output=True, text=True)
        enabled = enabled_proc.stdout.strip() == "enabled"
        active = active_proc.stdout.strip() == "active"
        if enabled and active:
            result["message"] = "fail2ban is enabled and running."
        else:
            result["status"] = "FAIL"
            result["message"] = f"fail2ban status issue: Boot: {'enabled' if enabled else 'disabled'}, Running: {'active' if active else 'stopped'}."
    except Exception as e:
        result["status"] = "FAIL"
        result["message"] = f"Error checking fail2ban: {e}"
    return result

def check_ssh_config():
    result = {"name": "SSH Configuration Check", "status": "PASS", "message": "", "category": "Security"}
    ssh_config = "/etc/ssh/sshd_config"
    issues = []
    if not os.path.isfile(ssh_config):
        result["status"] = "FAIL"
        result["message"] = f"SSH configuration file not found at {ssh_config}"
        return result

    try:
        with open(ssh_config, "r") as f:
            content = f.read()
    except Exception as e:
        result["status"] = "FAIL"
        result["message"] = f"Error reading SSH config: {e}"
        return result

    # Check PermitRootLogin is disabled
    permit_root = None
    for line in content.splitlines():
        if line.strip().lower().startswith("permitrootlogin"):
            parts = line.split()
            if len(parts) >= 2:
                permit_root = parts[1].strip()
            break
    if permit_root is None:
        issues.append("PermitRootLogin not explicitly set (default may allow root login).")
    elif permit_root.lower() == "yes":
        issues.append("PermitRootLogin is enabled.")
    
    # Check PasswordAuthentication is disabled
    password_auth = None
    for line in content.splitlines():
        if line.strip().lower().startswith("passwordauthentication"):
            parts = line.split()
            if len(parts) >= 2:
                password_auth = parts[1].strip()
            break
    if password_auth is None:
        issues.append("PasswordAuthentication not explicitly set (default may allow passwords).")
    elif password_auth.lower() == "yes":
        issues.append("PasswordAuthentication is enabled.")

    # Check that the SSH port is not the default port 22
    ssh_port = None
    for line in content.splitlines():
        if line.strip().lower().startswith("port"):
            parts = line.split()
            if len(parts) >= 2:
                ssh_port = parts[1].strip()
            break
    if ssh_port is None:
        # If not explicitly set, the default SSH port is 22
        ssh_port = "22"
    if ssh_port == "22":
        issues.append("SSH port is set to the default 22; consider using a non-standard port for enhanced security.")

    if issues:
        result["status"] = "FAIL"
        result["message"] = "SSH issues: " + "; ".join(issues) + ". Recommend: PermitRootLogin no, PasswordAuthentication no, and use a custom SSH port."
    else:
        result["message"] = "SSH configuration is secure."
    return result


def check_solana_logrotate():
    """Check for a Solana-related logrotate configuration."""
    result = {"name": "Solana Logrotate Check", "status": "PASS", "message": "", "category": "Security"}
    logrotate_dir = "/etc/logrotate.d"
    solana_patterns = ["sol", "solana", "solana-validator", "frankendancer", "firedancer"]
    found = False
    config_file = None
    if not shutil.which("logrotate"):
        result["status"] = "FAIL"
        result["message"] = "logrotate is not installed."
        return result
    if not os.path.isdir(logrotate_dir):
        result["status"] = "FAIL"
        result["message"] = "logrotate.d directory not found."
        return result
    for pattern in solana_patterns:
        candidate = os.path.join(logrotate_dir, pattern)
        if os.path.isfile(candidate):
            found = True
            config_file = candidate
            break
        for filename in os.listdir(logrotate_dir):
            if pattern in filename:
                found = True
                config_file = os.path.join(logrotate_dir, filename)
                break
        if found:
            break

    # Check if a Solana service appears active (to require a configuration)
    solana_running = False
    try:
        if shutil.which("systemctl"):
            proc = subprocess.run(["systemctl", "is-active", "solana"], capture_output=True, text=True)
            if proc.stdout.strip() == "active":
                solana_running = True
        if not solana_running:
            proc = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            if "solana" in proc.stdout.lower():
                solana_running = True
    except Exception:
        pass

    if found:
        result["message"] = f"Solana logrotate config found.."
    elif solana_running:
        result["status"] = "FAIL"
        result["message"] = "Solana service running but no logrotate config found."
    else:
        result["status"] = "WARNING"
        result["message"] = "No Solana logrotate config found (may be acceptable if Solana is not installed)."
    return result

def check_unattended_upgrades_disabled():
    """Ensure automatic updates are disabled."""
    result = {"name": "Automatic Updates Check", "status": "PASS", "message": "", "category": "Security"}
    enabled = False
    apt_based = False

    if shutil.which("apt") and os.path.isdir("/etc/apt/apt.conf.d"):
        apt_based = True
        try:
            proc = subprocess.run(["dpkg", "-l"], capture_output=True, text=True)
            if "unattended-upgrades" in proc.stdout:
                ua_proc = subprocess.run(["systemctl", "is-active", "unattended-upgrades"], capture_output=True, text=True)
                if ua_proc.stdout.strip() == "active":
                    enabled = True
                timer1 = subprocess.run(["systemctl", "is-enabled", "apt-daily.timer"], capture_output=True, text=True).stdout.strip()
                timer2 = subprocess.run(["systemctl", "is-enabled", "apt-daily-upgrade.timer"], capture_output=True, text=True).stdout.strip()
                if timer1 == "enabled" or timer2 == "enabled":
                    enabled = True
            else:
                result["message"] = "unattended-upgrades package not installed."
        except Exception as e:
            result["status"] = "FAIL"
            result["message"] = f"Error checking unattended-upgrades: {e}"
            return result

    # Also check for yum-cron or dnf-automatic on RHEL/Fedora systems
    if shutil.which("yum"):
        try:
            proc = subprocess.run(["rpm", "-q", "yum-cron"], capture_output=True, text=True)
            if proc.returncode == 0:
                ua_proc = subprocess.run(["systemctl", "is-active", "yum-cron"], capture_output=True, text=True)
                if ua_proc.stdout.strip() == "active":
                    enabled = True
        except Exception:
            pass

    if shutil.which("dnf"):
        try:
            proc = subprocess.run(["rpm", "-q", "dnf-automatic"], capture_output=True, text=True)
            if proc.returncode == 0:
                ua_proc = subprocess.run(["systemctl", "is-active", "dnf-automatic.timer"], capture_output=True, text=True)
                if ua_proc.stdout.strip() == "active":
                    enabled = True
        except Exception:
            pass

    if enabled:
        result["status"] = "FAIL"
        result["message"] = "Automatic update services are enabled."
    else:
        if apt_based:
            result["message"] = "Automatic update services are disabled."
    return result

def run_security_checks(skip_fail2ban=False, skip_ssh_check=False):
    """Run all security checks and return a list of results."""
    results = []
    if not skip_fail2ban:
        results.append(check_fail2ban())
    else:
        results.append({"name": "fail2ban Service Check", "status": "SKIPPED", "message": "fail2ban check skipped.", "category": "Security"})
    if not skip_ssh_check:
        results.append(check_ssh_config())
    else:
        results.append({"name": "SSH Configuration Check", "status": "SKIPPED", "message": "SSH check skipped.", "category": "Security"})
    results.append(check_solana_logrotate())
    results.append(check_unattended_upgrades_disabled())
    return results
