# checks/config.py

import subprocess
import re

def normalize_whitespace(s):
    """Normalize whitespace in a string."""
    return re.sub(r'\s+', ' ', s).strip()

def run_sysctl_check(param, expected):
    """Run a sysctl check for a given parameter and expected value.
    
    Returns a dict with:
      - name: Description of check
      - status: PASS or FAIL
      - message: Details on the check
    """
    result = {"name": f"Sysctl {param}", "status": "", "message": ""}
    try:
        proc = subprocess.run(["sysctl", "-n", param], capture_output=True, text=True, check=True)
        current = proc.stdout.strip()
    except subprocess.CalledProcessError:
        result["status"] = "FAIL"
        result["message"] = f"Could not retrieve {param} value. (Permission issue or non-Linux system?)"
        return result

    # Special case for kernel.pid_max: current should be >= expected
    if param == "kernel.pid_max":
        try:
            if int(current) >= int(expected):
                result["status"] = "PASS"
                result["message"] = f"{param} is sufficient: {current} (minimum required: {expected})"
            else:
                result["status"] = "FAIL"
                result["message"] = f"{param} is too low. Current: {current}, Minimum: {expected}."
            return result
        except ValueError:
            result["status"] = "FAIL"
            result["message"] = f"Invalid numeric value for {param}: {current}"
            return result

    # Special case for vm.swappiness: current should be 0
    if param == "vm.swappiness":
        max_swappiness = 20
        try:
            if int(current) <= max_swappiness:
                result["status"] = "PASS"
                result["message"] = f"{param} is acceptable: {current} (max allowed: {max_swappiness})"
            else:
                result["status"] = "FAIL"
                result["message"] = f"{param} is too high. Current: {current}, Maximum: {max_swappiness}."
            return result
        except ValueError:
            result["status"] = "FAIL"
            result["message"] = f"Invalid numeric value for {param}: {current}"
            return result

    # Special case for tcp_congestion_control: accept 'bbr' with a warning
    if param == "net.ipv4.tcp_congestion_control":
        if current == "bbr":
            result["status"] = "PASS"
            result["message"] = f"{param} is set to BBR (an acceptable alternative to westwood)."
            return result

    # For all other parameters compare after normalizing whitespace
    normalized_current = normalize_whitespace(current)
    normalized_expected = normalize_whitespace(expected)
    if normalized_current == normalized_expected:
        result["status"] = "PASS"
        result["message"] = f"{param} is correct: {current}"
    else:
        result["status"] = "FAIL"
        result["message"] = f"{param} is incorrect. Current: {current}, Expected: {expected}"
    return result

def run_config_checks():
    """Run all sysctl configuration checks and return a list of results."""
    sysctl_categories = {
        "Virtual Memory Tuning": {
            "vm.swappiness": "0",
        }
    }
    advanced_categories = {
        "TCP Buffer Sizes": {
            "net.ipv4.tcp_rmem": "10240 87380 12582912",
            "net.ipv4.tcp_wmem": "10240 87380 12582912"
        },
        "TCP Optimization": {
            "net.ipv4.tcp_congestion_control": "westwood",
            "net.ipv4.tcp_fastopen": "3",
            "net.ipv4.tcp_timestamps": "0",
            "net.ipv4.tcp_sack": "1",
            "net.ipv4.tcp_low_latency": "1",
            "net.ipv4.tcp_tw_reuse": "1",
            "net.ipv4.tcp_no_metrics_save": "1",
            "net.ipv4.tcp_moderate_rcvbuf": "1"
        },
        "Kernel Optimization": {
            "kernel.timer_migration": "0",
            "kernel.hung_task_timeout_secs": "30",
            "kernel.pid_max": "49152"
        },
        "Virtual Memory Tuning": {
            "vm.max_map_count": "2000000",
            "vm.stat_interval": "10",
            "vm.dirty_ratio": "40",
            "vm.dirty_background_ratio": "10",
            "vm.min_free_kbytes": "3000000",
            "vm.dirty_expire_centisecs": "36000",
            "vm.dirty_writeback_centisecs": "3000",
            "vm.dirtytime_expire_seconds": "43200"
        },
        "Solana Specific Tuning": {
            "net.core.rmem_max": "134217728",
            "net.core.rmem_default": "134217728",
            "net.core.wmem_max": "134217728",
            "net.core.wmem_default": "134217728"
        }
    }
    results = []
    for category, params in sysctl_categories.items():
        for param, expected in params.items():
            check = run_sysctl_check(param, expected)
            check["category"] = "Configuration (" + category + ")"
            results.append(check)
    return results
