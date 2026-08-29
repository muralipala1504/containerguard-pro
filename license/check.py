"""
ContainerGuard Pro License Check
Validates license for Pro features
"""

import os
import json
import requests
import logging

logger = logging.getLogger(__name__)

LICENSE_FILE = "/etc/containerguard/license.json"
PRO_REPO = "muralipala1504/containerguard-pro"
GITHUB_API = "https://api.github.com/repos/muralipala1504/containerguard-pro"

def check_license():
    """Check if Pro license is valid"""
    # 1. Check local license file
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, 'r') as f:
                license_data = json.load(f)
                if license_data.get("tier") == "pro":
                    return True
        except:
            pass
    
    # 2. Check GitHub repo access (if user has access)
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(GITHUB_API, headers=headers, timeout=5)
        if response.status_code == 200:
            return True
    except:
        pass
    
    return False

def get_pro_features():
    """Get list of Pro features"""
    if check_license():
        return {
            "slack_alerts": True,
            "auto_cleanup": True,
            "multi_host": True,
            "unlimited_history": True
        }
    return {}
