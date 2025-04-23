# checks/health.py

import subprocess
import glob
import os
import re

def check_cpu_governor():
    """Check that all CPUs are set to the 'performance' governor."""
    result = {"name": "CPU Governor Check", "status": "PASS", "message": "", "category": "Health"}
    expected = "performance"
    mismatches = []
    total_checkable = 0

    paths = glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor")
    for path in paths:
        try:
            with open(path, "r") as f:
                current = f.read().strip()
            cpu_num = re.search(r"cpu(\d+)", path).group(1)
            total_checkable += 1
            if current != expected:
                mismatches.append(f"CPU {cpu_num}={current}")
        except Exception:
            # If a core cannot be read, ignore or report it as busy
            pass

    if not mismatches:
        result["message"] = f"All {total_checkable} CPU cores set to '{expected}'."
    else:
        result["status"] = "FAIL"
        result["message"] = f"{len(mismatches)} of {total_checkable} cores are not set to '{expected}': " + ", ".join(mismatches)
    return result

"""Ensure that swap is disabled for optimal validator performance.

Swap space can cause significant performance degradation for validators due to:
- Increased latency from disk I/O when memory pages are swapped
- Interference with memory-intensive operations
- Potential for thrashing under high load
- Unpredictable performance characteristics

This check verifies that swap is completely disabled to maintain consistent,
high-performance operation of the validator node.
"""
def check_swap_disabled():

    """Ensure that swap is disabled."""
    result = {"name": "Swap Disabled Check", "status": "PASS", "message": "", "category": "Health"}
    swap_status = "disabled"
    try:
        proc = subprocess.run(["swapon", "--show"], capture_output=True, text=True)
        if proc.stdout.strip():
            swap_status = "enabled"
    except FileNotFoundError:
        if os.path.exists("/proc/swaps"):
            with open("/proc/swaps", "r") as f:
                lines = f.readlines()[1:]
                if lines:
                    swap_status = "enabled"
    if swap_status == "disabled":
        result["message"] = "Swap is disabled."
    else:
        result["status"] = "FAIL"
        result["message"] = "Swap is enabled."
    return result

def check_cpu_boost():
    """Check if CPU boost is enabled."""
    result = {"name": "CPU Boost Check", "status": "PASS", "message": "", "category": "Health"}
    boost_status = None
    boost_path = "/sys/devices/system/cpu/cpufreq/boost"
    intel_boost_path = "/sys/devices/system/cpu/intel_pstate/no_turbo"
    amd_boost_path = "/sys/devices/system/cpu/cpufreq/boost"
    if os.path.isfile(boost_path):
        try:
            with open(boost_path, "r") as f:
                value = f.read().strip()
            boost_status = "enabled" if value == "1" else "disabled"
        except Exception:
            boost_status = "unknown"
    elif os.path.isfile(intel_boost_path):
        try:
            with open(intel_boost_path, "r") as f:
                value = f.read().strip()
            boost_status = "enabled" if value == "0" else "disabled"  # Intel: no_turbo=0 means boost is enabled
        except Exception:
            boost_status = "unknown"
    elif os.path.isfile(amd_boost_path):
        try:
            with open(amd_boost_path, "r") as f:
                value = f.read().strip()
            boost_status = "enabled" if value == "1" else "disabled"
        except Exception:
            boost_status = "unknown"
    else:
        boost_files = glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_boost_freq")
        if boost_files:
            statuses = []
            for bf in boost_files:
                try:
                    with open(bf, "r") as f:
                        value = f.read().strip()
                    statuses.append(int(value) != 0)
                except Exception:
                    pass
            if statuses and all(statuses):
                boost_status = "enabled"
            else:
                boost_status = "disabled"
        else:
            result["status"] = "WARNING"
            result["message"] = "Could not determine CPU boost status."
            return result

    if boost_status == "enabled":
        result["message"] = "CPU boost is enabled."
    elif boost_status == "disabled":
        result["status"] = "FAIL"
        result["message"] = "CPU boost is disabled; expected enabled."
    else:
        result["status"] = "WARNING"
        result["message"] = "CPU boost status is unknown."
    return result

def check_pstate_driver():
    """Check if the CPU is using a p-state driver."""
    result = {"name": "CPU p-state Driver Check", "status": "PASS", "message": "", "category": "Health"}
    driver_file = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
    if os.path.isfile(driver_file):
        try:
            with open(driver_file, "r") as f:
                driver = f.read().strip()
            if "pstate" in driver.lower():
                result["message"] = f"Using p-state driver: {driver}"
            else:
                result["status"] = "FAIL"
                result["message"] = f"Not using p-state driver. Current: {driver}. Expected a p-state driver."
        except Exception as e:
            result["status"] = "FAIL"
            result["message"] = f"Error reading driver: {e}"
    else:
        result["status"] = "FAIL"
        result["message"] = "CPU scaling driver file not found."
    return result

def check_ntp_sync():
    """Check if NTP-based time synchronization is active."""
    result = {"name": "NTP Sync Check", "status": "FAIL", "message": "", "category": "Health"}
    ntp_synced = False
    sync_method = ""
    try:
        proc = subprocess.run(["timedatectl", "status"], capture_output=True, text=True)
        output = proc.stdout
        if "NTP service: active" in output or "System clock synchronized: yes" in output:
            ntp_synced = True
            sync_method = "timedatectl"
    except Exception:
        pass

    if ntp_synced:
        result["status"] = "PASS"
        result["message"] = f"Time sync is enabled via {sync_method}."
    else:
        result["message"] = "No active NTP synchronization detected. An NTP service is expected."
    return result

def check_package_updates():
    """Check for pending package updates (max allowed: 5)."""
    result = {"name": "Package Updates Check", "status": "PASS", "message": "", "category": "Health"}
    max_allowed = 5
    update_count = 0
    pkgmanager = None
    try:
        if subprocess.run(["which", "apt"], capture_output=True).returncode == 0:
            pkgmanager = "apt"
            subprocess.run(["apt-get", "update", "-qq"], capture_output=True)
            proc = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True)
            lines = [line for line in proc.stdout.splitlines() if "Listing..." not in line]
            update_count = len(lines)
        elif subprocess.run(["which", "dnf"], capture_output=True).returncode == 0:
            pkgmanager = "dnf"
            proc = subprocess.run(["dnf", "check-update", "--quiet"], capture_output=True, text=True)
            update_count = len([l for l in proc.stdout.splitlines() if l.strip()])
        elif subprocess.run(["which", "yum"], capture_output=True).returncode == 0:
            pkgmanager = "yum"
            proc = subprocess.run(["yum", "check-update", "--quiet"], capture_output=True, text=True)
            update_count = len([l for l in proc.stdout.splitlines() if l.strip()])
        elif subprocess.run(["which", "pacman"], capture_output=True).returncode == 0:
            pkgmanager = "pacman"
            subprocess.run(["pacman", "-Sy"], capture_output=True)
            proc = subprocess.run(["pacman", "-Qu"], capture_output=True, text=True)
            update_count = len(proc.stdout.splitlines())
        elif subprocess.run(["which", "zypper"], capture_output=True).returncode == 0:
            pkgmanager = "zypper"
            proc = subprocess.run(["zypper", "list-updates"], capture_output=True, text=True)
            update_count = len([l for l in proc.stdout.splitlines() if "|" in l])
        else:
            result["status"] = "WARNING"
            result["message"] = "Could not determine package manager."
            return result
    except Exception as e:
        result["status"] = "FAIL"
        result["message"] = f"Error checking package updates: {e}"
        return result

    if update_count <= max_allowed:
        result["message"] = f"{update_count} update(s) pending ({pkgmanager}). Maximum allowed: {max_allowed}."
    else:
        result["status"] = "FAIL"
        result["message"] = f"{update_count} update(s) pending ({pkgmanager}). Maximum allowed: {max_allowed}."
    return result

def check_reboot_required():
    """Check if a system reboot is required (Ubuntu/Debian)."""
    result = {"name": "Reboot Required Check", "status": "PASS", "message": "", "category": "Health"}
    if os.path.exists("/var/run/reboot-required"):
        result["status"] = "FAIL"
        msg = "System requires a reboot."
        if os.path.exists("/var/run/reboot-required.pkgs"):
            try:
                with open("/var/run/reboot-required.pkgs", "r") as f:
                    pkgs = f.read().strip()
                msg += f" Packages: {pkgs}"
            except Exception:
                pass
        result["message"] = msg
    else:
        result["message"] = "System does not require a reboot."
    return result

def run_health_checks():
    """Run all health-related checks and return a list of results."""
    results = []
    results.append(check_cpu_governor())
    # results.append(check_swap_disabled())
    results.append(check_cpu_boost())
    # results.append(check_pstate_driver())
    # results.append(check_ntp_sync())
    results.append(check_package_updates())
    results.append(check_reboot_required())
    return results
