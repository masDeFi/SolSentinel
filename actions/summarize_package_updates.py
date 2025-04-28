#!/usr/bin/env python3

import subprocess
import re
import sys

def run_command(cmd):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}", file=sys.stderr)
        sys.exit(1)

def parse_upgradable_packages():
    """Parse output of apt list --upgradable."""
    subprocess.run(["sudo", "apt-get", "update"], check=False, stdout=subprocess.DEVNULL)
    lines = run_command(["apt", "list", "--upgradable"])
    packages = []

    for line in lines:
        if not line or line.startswith("Listing..."):
            continue
        # cloud-init/focal-updates 24.4.1-0ubuntu0~20.04.2 all [upgradable from: 23.4.4-0ubuntu0~20.04.1]
        parts = line.split()
        pkg_repo = parts[0]
        new_version = parts[1]
        src = pkg_repo.split("/")[1] if "/" in pkg_repo else ""
        m = re.search(r"\[upgradable from: ([^\]]+)\]", line)
        old_version = m.group(1) if m else ""
        pkg_name = pkg_repo.split("/")[0]
        packages.append({
            "name": pkg_name,
            "new_version": new_version,
            "old_version": old_version,
            "source": src
        })
    return packages

def parse_semver(v):
    """Extract numeric version parts."""
    m = re.match(r"(\d+(?:\.\d+){0,2})", v)
    if not m:
        return [0, 0, 0]
    nums = [int(p) for p in m.group(1).split(".")]
    return nums + [0] * (3 - len(nums))

def classify_change(old, new):
    """Classify version change: major/minor/patch."""
    old_parts = parse_semver(old)
    new_parts = parse_semver(new)
    if new_parts[0] != old_parts[0]:
        return "major"
    if new_parts[1] != old_parts[1]:
        return "minor"
    if new_parts[2] != old_parts[2]:
        return "patch"
    return "patch"

def main():
    packages = parse_upgradable_packages()

    summary = {
        "security": [],
        "major": [],
        "minor": [],
        "patch": [],
    }

    for pkg in packages:
        entry = {
            "name": pkg["name"],
            "old_version": pkg["old_version"],
            "new_version": pkg["new_version"]
        }
        if "security" in pkg["source"]:
            summary["security"].append(entry)
        else:
            change_type = classify_change(pkg["old_version"], pkg["new_version"])
            summary[change_type].append(entry)

    print("## Package Update Summary\n")
    for group_name in ["security", "major", "minor", "patch"]:
        group = summary[group_name]
        print(f"**{group_name.capitalize()} updates:** {len(group)}")
        for pkg in group:
            print(f"  - {pkg['name']}: {pkg['old_version']} → {pkg['new_version']}")
        print()

if __name__ == "__main__":
    main()
