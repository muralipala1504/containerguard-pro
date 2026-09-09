"""
ContainerGuard Pro - Slack Alerts
"""

import os
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def send_slack_alert(action, resource, name, status, details=""):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return
    
    payload = {
        "text": f"🔐 *ContainerGuard Alert*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Action:* `{action}`\n*Resource:* `{resource}`\n*Name:* `{name}`\n*Status:* `{status}`\n*Time:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
                }
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Slack alert sent for {resource} {name}")
        else:
            logger.error(f"❌ Slack alert failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Slack alert error: {e}")
