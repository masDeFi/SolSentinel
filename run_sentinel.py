import argparse
import json
import os
import sys
import datetime
import psutil  # still used for drives
import re
from pathlib import Path

from checks import config, health, security
from post.post_to_discord import post_health_summary_to_discord

GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[0;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def parse_args():
    parser = argparse.ArgumentParser(description="Run validator health/config/security checks.")
    parser.add_argument("--skip-fail2ban", action="store_true", help="Skip the fail2ban check")
    parser.add_argument("--skip-package-updates", action="store_true", help="Skip the package updates check")
    parser.add_argument("--skip-ssh-check", action="store_true", help="Skip the SSH security configuration check")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress detailed output, only show summary")
    parser.add_argument("--env-file", help="Path to .env file containing Discord webhook URL", default=".env")
    return parser.parse_args()

def load_env_file(env_file):
    """Load environment variables from file."""
    if not os.path.exists(env_file):
        return {}
    
    env_vars = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip().strip('"\'')
    return env_vars

def get_cpu_info():
    """
    Reads /proc/cpuinfo and returns a dictionary with manufacturer and model.
    This works on Linux. If unavailable, returns 'Unknown'.
    """
    cpu_info = {"manufacturer": "Unknown", "model": "Unknown"}
    try:
        with open("/proc/cpuinfo", "r") as f:
            lines = f.readlines()
        # Try to get the first occurrence of vendor_id and model name
        for line in lines:
            if "vendor_id" in line and cpu_info["manufacturer"] == "Unknown":
                parts = line.split(":")
                if len(parts) > 1:
                    cpu_info["manufacturer"] = parts[1].strip()
            if "model name" in line and cpu_info["model"] == "Unknown":
                parts = line.split(":", 1)
                if len(parts) > 1:
                    cpu_info["model"] = parts[1].strip()
            # Once both are found, we can break out of the loop
            if cpu_info["manufacturer"] != "Unknown" and cpu_info["model"] != "Unknown":
                break
    except Exception:
        pass
    return cpu_info

def gather_meta_data():
    # Get the current UTC date/time in ISO 8601 format.
    run_datetime = datetime.datetime.utcnow().isoformat() + "Z"

    # Get CPU info instead of usage
    cpu_info = get_cpu_info()

    # Gather drive usage info for all partitions
    drives = {}
    for partition in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            drives[partition.mountpoint] = {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent_full": usage.percent
            }
        except Exception:
            continue

    meta = {
        "run_datetime": run_datetime,
        "cpu_info": cpu_info,
        "drives": drives
    }
    return meta

def main():
    args = parse_args()
    
    # Load environment variables
    env_vars = load_env_file(args.env_file)
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL') or env_vars.get('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print(f"{YELLOW}Warning: DISCORD_WEBHOOK_URL not set. Discord notifications will be skipped.{NC}")
    
    all_results = []
    
    config_results = config.run_config_checks()
    all_results.extend(config_results)
    
    health_results = health.run_health_checks()
    if args.skip_package_updates:
        health_results = [r for r in health_results if r["name"] != "Package Updates Check"]
        health_results.append({"name": "Package Updates Check", "status": "SKIPPED", "message": "Package updates check skipped.", "category": "Health"})
    all_results.extend(health_results)
    
    security_results = security.run_security_checks(skip_fail2ban=args.skip_fail2ban, skip_ssh_check=args.skip_ssh_check)
    all_results.extend(security_results)
    
    failure_count = sum(1 for r in all_results if r["status"] == "FAIL")
    
    if not args.quiet:
        for r in all_results:
            color = GREEN if r["status"] == "PASS" else RED if r["status"] == "FAIL" else YELLOW
            print(f"{BLUE}{r['name']}: {color}{r['status']}{NC}")
            print(f"    {r['message']}")
    
    print(f"\n{BLUE}Health check complete.{NC}")
    if failure_count == 0:
        print(f"{GREEN}All checks passed successfully.{NC}")
    else:
        print(f"{RED}{failure_count} check(s) failed.{NC}")
    
    report = {
        "meta": gather_meta_data(),
        "results": {
            "config_results": config_results,
            "health_results": health_results,
            "security_results": security_results
        }
    }
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "latest_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    if webhook_url:
        post_health_summary_to_discord(report, webhook_url)
    sys.exit(0 if failure_count == 0 else 1)

if __name__ == "__main__":
    main()
