import os
import json

LICENSE_FILE = "/etc/containerguard/license.json"

def check_license():
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, 'r') as f:
                data = json.load(f)
                return data.get("tier") == "pro"
        except:
            return False
    return False

def get_features():
    if check_license():
        return {"slack_alerts": True}
    return {"slack_alerts": False}
