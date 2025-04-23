# Validator Health Check

This project performs a series of health, configuration, and security checks on your validator. The results are output in JSON format and can be posted to your Discord.

## Coming soon  
- More detailed checks
- More notifcation options
- Package update summaries
- Suggested actions


## Project Structure
```
/solana-validoctor
├── README.md
├── .env                 # Your Discord webhook configuration
├── .env.example         # Template for .env file
├── checks/
│   ├── health.py
│   ├── config.py
│   └── security.py
├── run_checks.py
├── output/
│   └── latest_report.json
└── post/
    └── post_to_discord.py
``` 


## Usage

### Discord Setup
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

### Running Checks

Run the main script with:

```bash
python3 run_checks.py [OPTIONS]  
```

Options include:

--skip-fail2ban Skip the fail2ban check  
--skip-package-updates Skip the package updates check  
--skip-ssh-check Skip the SSH security configuration check  
-q or --quiet Suppress detailed output and only show final summary  
--env-file Path to custom .env file (default: .env)

Make sure the script is run with sufficient permissions so that it can access system information and run commands like sysctl.    


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


  
## Contributing
This project is open source—feel free to review and contribute!
Reach out on X or Discord to connect.