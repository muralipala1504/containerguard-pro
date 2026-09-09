"""
ContainerGuard Audit Logs
Tracks all user actions for compliance and debugging
"""

import os
import json
import csv
from datetime import datetime

AUDIT_FILE = "/tmp/containerguard_audit.json"

def log_action(user, action, resource, details, status="success"):
    """Log an action to the audit file"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "action": action,
        "resource": resource,
        "details": details,
        "status": status
    }
    
    logs = []
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, 'r') as f:
                logs = json.load(f)
        except:
            pass
    
    logs.append(entry)
    
    if len(logs) > 1000:
        logs = logs[-1000:]
    
    with open(AUDIT_FILE, 'w') as f:
        json.dump(logs, f, indent=2)
    
    return entry

def get_audit_logs(limit=50):
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, 'r') as f:
                logs = json.load(f)
                return logs[-limit:] if len(logs) > limit else logs
        except:
            return []
    return []

def get_audit_logs_by_user(user, limit=50):
    logs = get_audit_logs(1000)
    user_logs = [l for l in logs if l.get('user') == user]
    return user_logs[-limit:] if len(user_logs) > limit else user_logs

def export_audit_logs_json():
    """Export all audit logs as JSON"""
    logs = get_audit_logs(10000)
    return json.dumps(logs, indent=2)

def export_audit_logs_csv():
    """Export all audit logs as CSV"""
    logs = get_audit_logs(10000)
    if not logs:
        return ""
    
    output = "Timestamp,User,Action,Resource,Status,Details\n"
    for log in logs:
        output += f"{log.get('timestamp', '')},{log.get('user', '')},{log.get('action', '')},{log.get('resource', '')},{log.get('status', '')},{log.get('details', '')}\n"
    return output
