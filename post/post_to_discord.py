# post/post_to_discord.py

import json
import requests

def raw_post_to_discord(report_path, webhook_url):
    """
    Post the JSON report to Discord via a webhook.
    
    report_path: Path to the JSON report file.
    webhook_url: Discord webhook URL.
    """
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
    except Exception as e:
        print(f"Error reading report: {e}")
        return

    message_lines = ["**Validator Health Report**\n"]
    for check in report:
        line = f"- **{check['name']}**: {check['status']} — {check['message']}"
        message_lines.append(line)
    message = "\n".join(message_lines)

    data = {"content": message}
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code == 204:
            print("Successfully posted report to Discord.")
        else:
            print(f"Failed to post report (HTTP {response.status_code}).")
    except Exception as e:
        print(f"Error posting to Discord: {e}")


import requests

def post_health_summary_to_discord(health_data: dict, webhook_url: str):
    def format_section(title, results):
        lines = [f"**{title}**"]
        for item in results:
            icon = "✅" if item["status"] == "PASS" else "❌"
            lines.append(f"- {icon} {item['name']}: {item['message']}")
        return "\n".join(lines)

    # Parse grouped results
    config = format_section("🛠️ Configuration", health_data["results"].get("config_results", []))
    health = format_section("🧠 Health", health_data["results"].get("health_results", []))
    security = format_section("🔐 Security", health_data["results"].get("security_results", []))

    # Compose final message
    message = "\n".join([
        "📡 **Validator Health Check Summary**",
        "",
        config,
        "",
        health,
        "",
        security
    ])

    # Post to Discord webhook
    response = requests.post(webhook_url, json={"content": message})
    if response.status_code != 204:
        raise Exception(f"Discord webhook failed with status {response.status_code}: {response.text}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python post_to_discord.py <report_path> <webhook_url>")
    else:
        post_to_discord(sys.argv[1], sys.argv[2])
