"""
ContainerGuard Pro - Slack Alerts
Sends notifications to Slack when containers are restarted
"""

import os
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SlackAlert:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        if not self.webhook_url:
            logger.warning("⚠️ Slack webhook URL not configured. Alerts disabled.")
    
    def send_alert(self, container_name, action, status, message=None):
        """Send alert to Slack"""
        if not self.webhook_url:
            return False
        
        if message is None:
            message = f"Container `{container_name}` was **{action}** - Status: `{status}`"
        
        payload = {
            "text": f"🚨 *ContainerGuard Alert*",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Container:* `{container_name}`\n*Action:* `{action}`\n*Status:* `{status}`\n*Time:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "🔐 *ContainerGuard Pro* - Autonomous Docker Agent"
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Slack alert sent for {container_name}")
                return True
            else:
                logger.error(f"❌ Slack alert failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Slack alert error: {e}")
            return False
