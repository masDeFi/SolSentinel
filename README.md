# SolSentinel

**SolSentinel** is an intelligent monitoring and advisory system for Solana validators. It performs health, configuration, and security checks on your validator, helping you maintain high performance, minimize downtime, and protect your stakers.  

#### SolSentinel helps you:

- Detect early signs of performance degradation  
- Identify configuration or system issues
- Monitor validator security posture
- Stay proactive to protect your stakers and uptime
- Build trust with your stakers through transparency and reliability

## Coming soon  
- Advanced checks
- More notifcation options
- Package update summaries
- Action suggestions

### Current Directory Structure

/mnt
  - /ledger
  - /account

/home/user/code
  - firedancer/

/home/user/
  - mount-drives.sh 
  - (simlink)active-fd-config.toml->fd-config.toml
  - logs/ 
  - /SolSentinal 

Files in /home/user store server specific configs 
## Project Structure
```
/SolSentinel
├── README.md
├── .env                 # Your Discord webhook configuration
├── .env.example         # Template for .env file
├── checks/
│   ├── health.py
│   ├── config.py
│   └── security.py
├── run_sentinel.py
├── output/
│   └── latest_report.json
└── post/
    └── post_to_discord.py
``` 


## Usage
1. Clone the repo   
2. Use the scripts  

### Running Checks

Run the main script with:

```bash
python3 run_sentinel.py [OPTIONS]  
```

Options include:

--skip-fail2ban Skip the fail2ban check  
--skip-package-updates Skip the package updates check  
--skip-ssh-check Skip the SSH security configuration check  
-q or --quiet Suppress detailed output and only show final summary  
--env-file Path to custom .env file (default: .env)

Make sure the script is run with sufficient permissions so that it can access system information and run commands like sysctl.    

### Discord Setup (Optional)
1. In the root directory (`config-check/`), copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and add your Discord webhook URL:
   ```
   DISCORD_WEBHOOK_URL="your-discord-webhook-url-here"
   ```
   
   You can also set the webhook URL as an environment variable:
   ```bash
   export DISCORD_WEBHOOK_URL="your-discord-webhook-url-here"
   ```

## The Checks  

#### Package Updates Check  
Ensures the number of pending OS package updates stays within an acceptable threshold.  

- **Purpose:** Up to date packages are critical for security and stability.  
- **Recommended Action:** Regularly apply updates to keep the system fully patched. However, don't use auto update as you need to review changelogs and ensure change only occur in maintenance windows.

---

#### Reboot Required Check  
Detects whether a system reboot is needed to complete the installation of critical updates (such as a new kernel or core library).  

- **Purpose:** Guarantees that all security fixes and functionality improvements are actually active by confirming that any required reboot has been performed.  
- **Recommended Action:** Schedule and perform a reboot whenever this check reports "required" to ensure the system is running the latest code.  

## Flows
### Update Firedancer flow  

For the complete safety-gated workflow:

```sh
cd ~/SolSentinel/actions

# Run the complete safety-gated update. Approve the deps.sh prompt if asked.
# The script refuses to stop a running validator that is using the primary
# identity, then stops, updates, builds, verifies, configures, restarts, checks
# identity again, and streams catchup progress until the validator is caught up.
./complete_update_firedancer.sh v<version>
```

For unusual tags whose `fdctl version` output differs from the tag, pass the
expected output as a second argument. `SOLANA_RPC_URL` can override the Solana
CLI's configured RPC during the catchup wait:

```sh
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com \
  ./complete_update_firedancer.sh v<tag> <expected-fdctl-version>
```

The original staged workflow remains available as a fallback:

```sh
sudo systemctl stop frankendancer.service
./update-firedancer.sh v<version>
./make-firedancer.sh
~/code/firedancer/build/native/gcc/bin/fdctl version
./configure-firedancer.sh
sudo systemctl start frankendancer.service
sudo systemctl status frankendancer.service
```

Neither workflow reboots the server. If the complete update fails after
stopping the service, it deliberately leaves the service stopped rather than
starting an unverified or unconfigured build. Reboot only when an OS update or
configuration change separately requires one.

If you see a log like: ***pack cpu 5 has hyperthread pair cpu 29 which should be offline. Proceeding but performance may be reduced.***. Fix with the command below for each instance:
```sh
echo 0 | sudo tee /sys/devices/system/cpu/cpu29/online
./start-firedancer.sh  
```
  
## Contributing
This project is open source. Please review and contribute!
Reach out on [X (@MAS_DeFi)](https://x.com/MAS_DeFi) or [Discord](https://discordapp.com/users/masdefi_62609) to connect.
