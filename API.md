# 🔌 ContainerGuard Pro API Reference

Complete API documentation for ContainerGuard Pro's internal interfaces, persistent history, and extensibility points.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Agent API](#agent-api)
3. [Container Actions API](#container-actions-api)
4. [Dashboard API](#dashboard-api)
5. [Persistent History API](#persistent-history-api)
6. [Audit Log API](#audit-log-api)
7. [Pro Features API](#pro-features-api)
8. [Multi-Host API](#multi-host-api)
9. [Slack Webhook Integration](#slack-webhook-integration)
10. [Error Codes](#error-codes)
11. [Examples](#examples)

---

## Overview

ContainerGuard Pro provides several interfaces for integration:

| Interface | Purpose | Protocol |
|-----------|---------|----------|
| **Agent Core** | Monitoring and actions | Python API |
| **Container Actions** | Docker container management | Python API |
| **Dashboard** | Web UI | HTTP (Gradio) |
| **Audit Log** | Action logging | JSON file |
| **Pro Features** | Slack alerts, auto-cleanup | Python API |
| **Multi-Host** | Multiple Docker hosts | JSON config |

---

## Agent API

### ContainerGuardAgent Class

```python
class ContainerGuardAgent:
    def __init__(self, docker_host='unix:///var/run/docker.sock'):
        """
        Initialize the agent with a Docker host.

        Args:
            docker_host (str): Docker daemon URL
                - Local: 'unix:///var/run/docker.sock'
                - Remote: 'tcp://host:2375'
                - SSH: 'ssh://user@host'
        """
        pass

    def get_all_containers(self) -> list:
        """
        Get all containers (including stopped).

        Returns:
            list: List of Docker container objects
        """
        pass

    def check_and_heal(self) -> tuple:
        """
        Check container health and heal if needed.

        Returns:
            tuple: (status_report, restarted_count)
                - status_report: list of dicts with 'name' and 'status'
                - restarted_count: number of containers restarted
        """
        pass

    def run_once(self) -> list:
        """
        Run a single monitoring cycle.

        Returns:
            list: Container status reports
        """
        pass
```

### Usage Example

```python
from agent.core import ContainerGuardAgent

# Initialize agent
agent = ContainerGuardAgent('tcp://192.168.217.165:2375')

# Run a monitoring cycle
results = agent.run_once()

# Output container status
for container in results:
    print(f"{container['name']}: {container['status']}")
```

---

## Container Actions API

### ContainerActions Class

```python
from agent.actions import ContainerActions
import docker

client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
actions = ContainerActions(client)
```

### Methods

#### restart_container()

```python
def restart_container(self, container_id: str) -> bool:
    """
    Restart a container.

    Args:
        container_id (str): Container ID or name

    Returns:
        bool: True if successful, False otherwise
    """
```

#### stop_container()

```python
def stop_container(self, container_id: str) -> bool:
    """
    Stop a running container.

    Args:
        container_id (str): Container ID or name

    Returns:
        bool: True if successful, False otherwise
    """
```

#### get_history()

```python
def get_history(self) -> list:
    """
    Get action history from JSON file.

    Returns:
        list: List of action dicts with timestamp, action, container, status
    """
```

### Usage Example

```python
from agent.actions import ContainerActions
import docker

client = docker.DockerClient(base_url='tcp://192.168.217.165:2375')
actions = ContainerActions(client)

# Restart a container
if actions.restart_container('test-nginx'):
    print("✅ Container restarted successfully")
else:
    print("❌ Failed to restart container")

# Get action history
history = actions.get_history()
for action in history[-5:]:
    print(f"{action['timestamp']}: {action['action']} {action['container']}")
```

---

## Dashboard API

### Gradio Endpoints

The dashboard exposes the following functions internally:

#### refresh()

```python
def refresh():
    """
    Fetch latest container status and action history from JSON.

    Returns:
        tuple: (nodes_text, pods_text, history_text)
            - nodes_text: Markdown formatted node list with container counts
            - pods_text: Markdown formatted container list with host labels
            - history_text: Markdown formatted recent actions
    """
    pass
```

#### restart_container()

```python
def restart_container(name: str) -> str:
    """
    Manually restart a container across all hosts.

    Args:
        name (str): Name of container to restart

    Returns:
        str: Success/failure message with host information
    """
    pass
```

#### export_json()

```python
def export_json() -> str:
    """
    Export audit logs as JSON.

    Returns:
        str: JSON formatted audit logs
    """
    pass
```

#### export_csv()

```python
def export_csv() -> str:
    """
    Export audit logs as CSV.

    Returns:
        str: CSV formatted audit logs with headers
    """
    pass
```

### HTTP Interface (Gradio)

```bash
# Access the dashboard
GET http://<agent-ip>:7860/

# Components are served via:
# - / (main page)
# - /gradio/ (Gradio static assets)
# - /api/ (Gradio API endpoints)
```

---

## Persistent History API

### History File Location

```bash
/tmp/containerguard_history.json
```

### File Format

```json
[
  {
    "timestamp": "2026-09-11T05:35:57.986681",
    "action": "restart",
    "container": "test-postgres",
    "host": "vm2-worker",
    "status": "success"
  }
]
```

### Reading History

```python
import json

def get_history():
    """Read history from JSON file"""
    try:
        with open('/tmp/containerguard_history.json', 'r') as f:
            return json.load(f)
    except:
        return []
```

### Writing History

```python
import json
from datetime import datetime

def add_action(action_type, container_name, status, host=None):
    """Add an action to history"""
    history = get_history()
    entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action_type,
        'container': container_name,
        'status': status
    }
    if host:
        entry['host'] = host
    history.append(entry)
    with open('/tmp/containerguard_history.json', 'w') as f:
        json.dump(history, f, indent=2)
```

### Action Types

| Action | Description |
|--------|-------------|
| `restart` | Container restarted |
| `stop` | Container stopped (manual) |
| `cleanup` | Unused containers removed |
| `error` | An error occurred |

---

## Audit Log API

### Audit File Location

```bash
/tmp/containerguard_audit.json
```

### File Format

```json
[
  {
    "timestamp": "2026-09-11T07:18:44.566260",
    "user": "system",
    "action": "auto-heal",
    "resource": "vm2-worker:test-nginx",
    "details": "Container auto-restarted",
    "status": "success"
  }
]
```

### API Functions

```python
from audit import log_action, get_audit_logs, export_audit_logs_json, export_audit_logs_csv

# Log an action
log_action(
    user="user",
    action="restart",
    resource="vm2-worker:test-nginx",
    details="Manual restart from dashboard",
    status="success"
)

# Get recent logs
logs = get_audit_logs(limit=10)
for log in logs:
    print(f"{log['timestamp']} - {log['user']} - {log['action']} {log['resource']}")

# Export as JSON
json_output = export_audit_logs_json()

# Export as CSV
csv_output = export_audit_logs_csv()
```

### CSV Format

```
Timestamp,User,Action,Resource,Status,Details
2026-09-11T07:18:44.566260,test-user,restart,test-nginx,success,Manual test action
```

---

## Pro Features API

### License Validation

```python
from license import check_license

# Check if Pro license is valid
is_pro = check_license()
# Returns: True if valid Pro license, False otherwise
```

### License File Format (`/etc/containerguard/license.json`)

```json
{
  "tier": "pro",
  "issued_at": "2026-09-09",
  "expires_at": "2027-09-09"
}
```

### Slack Alerts (Pro)

```python
from pro_agent.slack import SlackAlert

# Initialize Slack alert
slack = SlackAlert()

# Send alert
slack.send_alert(
    container_name="test-nginx",
    action="restarted",
    status="success"
)
```

### Auto-Cleanup (Pro)

```python
from pro_agent.cleanup import AutoCleanup
import docker

client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
cleanup = AutoCleanup(client)

# Run cleanup
result = cleanup.run()
# Returns: {'images': 0, 'volumes': 1, 'build_cache': 0, 'space_freed': 0}
```

### Trigger Cleanup Manually

```bash
python -c "
from agent.actions import ContainerActions
import docker
client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
actions = ContainerActions(client)
result = actions.run_cleanup()
print('Cleanup result:', result)
"
```

---

## Multi-Host API

### Hosts Configuration

**File:** `/etc/containerguard/hosts.conf`

**Format:**

```json
{
  "hosts": [
    {"name": "local", "host": "unix:///var/run/docker.sock"},
    {"name": "vm2-worker", "host": "tcp://192.168.217.165:2375"},
    {"name": "vm3-worker", "host": "tcp://192.168.217.166:2375"}
  ]
}
```

### Add a New Host

```bash
# Edit hosts.conf
sudo vi /etc/containerguard/hosts.conf

# Restart agent
sudo systemctl restart containerguard-pro
```

### Verify Hosts

```bash
sudo tail -20 /var/log/containerguard-pro.log | grep -i "connected\|host"
```

**Expected:**

```
✅ Connected to local (Docker 29.8.0)
✅ Connected to vm2-worker (Docker 29.8.0)
```

---

## Slack Webhook Integration

### Configuration

⚠️ **Security Note:** Never commit Slack webhook URLs to GitHub!

```bash
# Add webhook to .env file
echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL" >> ~/containerguard-pro/.env

# Restart service
sudo systemctl restart containerguard-pro
```

### Message Format

```json
{
  "text": "🚨 Container Restart Alert",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Container:* `test-postgres`\n*Action:* Restarted\n*Host:* vm2-worker\n*Time:* 2026-09-11 12:22:14"
      }
    }
  ]
}
```

### Example Slack Message

```
🚨 ContainerGuard Alert
Container: test-postgres
Action: restarted
Status: success
Host: vm2-worker
Time: 2026-09-11 12:22:14
```

---

## Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `E001` | Docker connection failed | Check `DOCKER_HOST` and network |
| `E002` | Container not found | Verify container name/ID |
| `E003` | Permission denied | Check SELinux/file permissions |
| `E004` | Action cooldown active | Wait for cooldown to expire |
| `E005` | JSON history read/write error | Check `/tmp` permissions |
| `E006` | Configuration error | Validate JSON syntax |
| `E007` | Webhook failed | Check webhook URL and network |
| `E008` | Pro license invalid | Check `/etc/containerguard/license.json` |

---

## Examples

### Example 1: Basic Monitoring

```python
from agent.core import ContainerGuardAgent

# Initialize agent
agent = ContainerGuardAgent('tcp://192.168.217.165:2375')

# Run a monitoring cycle
results = agent.run_once()

# Print results
for r in results:
    print(f"Container: {r['name']}")
    print(f"Status: {r['status']}")
    print("---")
```

### Example 2: Reading Audit Logs

```python
from audit import get_audit_logs

# Get last 10 actions
logs = get_audit_logs(10)
for log in logs:
    print(f"{log['timestamp']}: {log['user']} - {log['action']} {log['resource']}")
```

### Example 3: Manual Container Management

```python
from agent.actions import ContainerActions
import docker

client = docker.DockerClient(base_url='tcp://192.168.217.165:2375')
actions = ContainerActions(client)

# Restart a container
if actions.restart_container('test-postgres'):
    print("✅ Container restarted successfully")
else:
    print("❌ Failed to restart container")
```

### Example 4: Custom Webhook Integration

```python
import requests
from agent.core import ContainerGuardAgent

agent = ContainerGuardAgent('tcp://192.168.217.165:2375')

def send_event(event_data):
    """Send event to external API"""
    webhook_url = 'https://my-api.example.com/events'
    requests.post(webhook_url, json=event_data)

# Run monitoring cycle
results = agent.run_once()

# Send events for exited containers
for r in results:
    if r['status'] == 'exited':
        send_event({
            'event': 'container_exited',
            'container': r['name'],
            'timestamp': datetime.now().isoformat()
        })
```

### Example 5: Custom Rule Extension

```python
from agent.core import ContainerGuardAgent

class CustomAgent(ContainerGuardAgent):
    def check_and_heal(self):
        """Custom monitoring logic"""
        containers = self.get_all_containers()
        restarted_count = 0

        for container in containers:
            status = container.status
            name = container.name

            # Custom rule: Restart containers running > 24h
            if status == 'running':
                uptime = container.attrs['State']['StartedAt']
                if uptime > 24 * 60 * 60:  # 24 hours
                    self.actions.restart_container(container.id)
                    restarted_count += 1

            # Standard auto-heal for exited containers
            elif status == 'exited':
                self.actions.restart_container(container.id)
                restarted_count += 1

        return restarted_count
```

---

## Integration Patterns

### Pattern 1: Agent as a Library

```python
# embed.py
from agent.core import ContainerGuardAgent

def my_application():
    agent = ContainerGuardAgent()
    while True:
        results = agent.run_once()
        process_results(results)
        time.sleep(60)
```

### Pattern 2: Agent as a Service

```bash
# Using systemd
sudo systemctl start containerguard-pro
sudo systemctl status containerguard-pro
sudo journalctl -u containerguard-pro -f
```

### Pattern 3: Reading Audit Logs from External Script

```python
# monitor_audit.py
import json
import time

def tail_audit():
    """Continuously monitor audit file"""
    last_count = 0
    while True:
        try:
            with open('/tmp/containerguard_audit.json', 'r') as f:
                audit = json.load(f)
            if len(audit) > last_count:
                new_actions = audit[last_count:]
                for action in new_actions:
                    print(f"New action: {action}")
                last_count = len(audit)
        except:
            pass
        time.sleep(5)

if __name__ == "__main__":
    tail_audit()
```

---

## Future API Extensions

### RESTful API (Planned)

```
GET    /api/v1/containers          # List all containers
GET    /api/v1/containers/{id}     # Get container details
POST   /api/v1/containers/{id}/restart
POST   /api/v1/containers/{id}/stop
GET    /api/v1/history             # Get action history
GET    /api/v1/audit               # Get audit logs
GET    /api/v1/health              # Health check
```

### Prometheus Exporter (Planned)

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'containerguard'
    static_configs:
      - targets: ['localhost:8000']
```

---

## Testing

```python
# test_api.py
import unittest
from agent.core import ContainerGuardAgent

class TestAgentAPI(unittest.TestCase):
    def setUp(self):
        self.agent = ContainerGuardAgent('tcp://192.168.217.165:2375')

    def test_get_containers(self):
        containers = self.agent.get_all_containers()
        self.assertGreater(len(containers), 0)

    def test_check_and_heal(self):
        results, count = self.agent.check_and_heal()
        self.assertIsInstance(results, list)
        self.assertIsInstance(count, int)

    def test_audit_file(self):
        import os
        self.assertTrue(os.path.exists('/tmp/containerguard_audit.json'))
```

---

## 📚 Related Documentation

- **README.md** - Project overview
- **INSTALL.md** - Installation guide
- **ARCHITECTURE.md** - Technical architecture
- **TROUBLESHOOTING.md** - Common issues and fixes

---

## 🤝 Contributing

If you'd like to extend the API, please:

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Write tests
5. Submit a Pull Request
