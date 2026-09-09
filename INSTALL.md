# 🔧 ContainerGuard Pro Installation Guide

Detailed step-by-step instructions for installing ContainerGuard Pro on AlmaLinux 9, Ubuntu 22.04+, or RHEL-based systems.

---

## 📋 Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | AlmaLinux 8+, Ubuntu 20.04+ | AlmaLinux 9 |
| **CPU** | 2 cores | 4 cores |
| **RAM** | 2 GB | 4 GB |
| **Disk** | 10 GB | 20 GB |
| **Docker** | **Auto-installed by installer** | Latest |
| **Python** | 3.9+ | 3.9+ |

> **Note**: The installer **automatically installs Docker** if it's not present. You don't need to install Docker manually.

---

## 🚀 Quick Install (Recommended)

### One-Line Installation

```bash
curl -sSL https://raw.githubusercontent.com/muralipala1504/containerguard-pro/main/install.sh | bash

What the Installer Does
The installer will:

✅ Check prerequisites (Docker, Python, OS)

✅ Clone the repository

✅ Create Python virtual environment

✅ Install dependencies

✅ Configure SELinux context (if enforcing)

✅ Ask for Docker configuration (local/remote)

✅ Ask for Pro license setup

✅ Install systemd services

✅ Open firewall port 7860

✅ Start the agent and dashboard

📦 Manual Installation (Advanced)
1. Clone the Repository
cd ~
git clone https://github.com/muralipala1504/containerguard-pro.git
cd containerguard-pro

2. Create Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Verify Python path
which python
# Should show: /home/username/containerguard-pro/venv/bin/python

3. Install Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import docker; print('✅ Docker SDK installed')"
python -c "import gradio; print('✅ Gradio installed')"
4. Configure SELinux (if enabled)
⚠️ Critical Step for AlmaLinux/RHEL:
# Check SELinux status
getenforce

# If enforcing, apply context rules to venv binaries
sudo chcon -R -t bin_t venv/bin/

# Apply context to wrapper scripts
sudo chcon -t bin_t agent/run-pro.sh
sudo chcon -t bin_t dashboard/run.sh

# Verify
ls -Z venv/bin/python
# Should show: unconfined_u:object_r:bin_t:s0
5. Configure Docker Connection
Option A: Local Docker (Same Machine)
# Use default Docker socket
export DOCKER_HOST=unix:///var/run/docker.sock
Option B: Remote Docker (Different Machine)

On the worker VM (where containers run):
# Enable Docker API
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo tee /etc/systemd/system/docker.service.d/override.conf << 'DOCKEREOF'
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0:2375
DOCKEREOF

sudo systemctl daemon-reload
sudo systemctl restart docker

# Open firewall port
sudo firewall-cmd --add-port=2375/tcp --permanent
sudo firewall-cmd --reload
On the control VM (where ContainerGuard runs):
# Configure Multi-Host
sudo mkdir -p /etc/containerguard
sudo tee /etc/containerguard/hosts.conf << 'EOF'
{
  "hosts": [
    {"name": "vm1-agent", "host": "unix:///var/run/docker.sock"},
    {"name": "vm2-worker", "host": "tcp://192.168.217.165:2375"}
  ]
}
EOF
6. Configure Pro License
sudo mkdir -p /etc/containerguard
sudo tee /etc/containerguard/license.json << 'EOF'
{
  "tier": "pro",
  "issued_at": "2026-09-09",
  "expires_at": "2027-09-09"
}
EOF

# Verify license
cat /etc/containerguard/license.json
7. Set Up as Systemd Services
Step 1: Copy service files
sudo cp deploy/containerguard.service /etc/systemd/system/
sudo cp deploy/containerguard-dashboard.service /etc/systemd/system/
Step 2: Update paths to point to pro (if needed)
sudo sed -i 's|containerguard-new|containerguard-pro|g' /etc/systemd/system/containerguard.service
sudo sed -i 's|containerguard-new|containerguard-pro|g' /etc/systemd/system/containerguard-dashboard.service
Step 3: Reload and start services
sudo systemctl daemon-reload
sudo systemctl enable containerguard
sudo systemctl enable containerguard-dashboard
sudo systemctl start containerguard
sudo systemctl start containerguard-dashboard
Step 4: Verify services
sudo systemctl status containerguard
sudo systemctl status containerguard-dashboard
8. Configure Slack Alerts (Pro)
⚠️ Security Note: Never commit Slack webhook URLs to GitHub!
# Add webhook to .env file (never commit this!)
echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL" >> /home/ruser/containerguard-pro/.env

# Restart service
sudo systemctl restart containerguard
9. Open Firewall Port
# Firewalld
sudo firewall-cmd --add-port=7860/tcp --permanent
sudo firewall-cmd --reload

# UFW
sudo ufw allow 7860/tcp

# Verify
sudo firewall-cmd --list-ports
🔧 Wrapper Scripts Explained
ContainerGuard Pro uses wrapper scripts to handle SELinux and environment variables:

Agent Wrapper (agent/run-pro.sh)

#!/bin/bash
export PYTHONPATH="/home/ruser/containerguard-pro:$PYTHONPATH"
cd /home/ruser/containerguard-pro
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi
source venv/bin/activate
exec python agent/runner.py

Dashboard Wrapper (dashboard/run.sh)
#!/bin/bash
cd /home/ruser/containerguard-pro
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi
source venv/bin/activate
python dashboard/app.py
🌐 Dashboard Access
# Access the dashboard
http://<your-ip>:7860

# Check if dashboard is running
sudo systemctl status containerguard-dashboard

# View dashboard logs
sudo journalctl -u containerguard-dashboard -f
🔍 Verification
Verify Agent is Running
# Check service status
sudo systemctl status containerguard

# Check logs
sudo tail -20 /var/log/containerguard.log

Expected output:
2026-09-09 11:25:53,482 - INFO - ✅ local-test on vm2-worker: RUNNING
2026-09-09 11:25:53,482 - INFO - ✅ test-app on vm2-worker: RUNNING
2026-09-09 11:25:53,483 - INFO - 📊 Monitored containers across 2 hosts, restarted 0
2026-09-09 11:25:53,483 - INFO - ✅ Monitoring cycle completed
Verify Pro Features

# Check if Pro features are enabled
sudo grep -i "pro" /var/log/containerguard.log | tail -5

# Check license
python -c "import json; f=open('/etc/containerguard/license.json'); print(json.load(f))"
Verify Multi-Host
sudo cat /etc/containerguard/hosts.conf
sudo tail -20 /var/log/containerguard.log | grep -i "connected\|host"
🐛 Common Issues & Solutions
SELinux Blocking Execution
Symptoms: Service fails with status=203/EXEC or Permission denied

Solution:
# Apply SELinux context to venv binaries
sudo chcon -R -t bin_t /home/ruser/containerguard-pro/venv/bin/

# Apply to wrapper scripts
sudo chcon -t bin_t /home/ruser/containerguard-pro/agent/run-pro.sh
sudo chcon -t bin_t /home/ruser/containerguard-pro/dashboard/run.sh

# Restart services
sudo systemctl restart containerguard
sudo systemctl restart containerguard-dashboard

Service Points to Wrong Directory
Symptoms: Service shows errors about missing files or uses containerguard-new instead of containerguard-pro

Solution:
# Update service files
sudo sed -i 's|containerguard-new|containerguard-pro|g' /etc/systemd/system/containerguard.service
sudo sed -i 's|containerguard-new|containerguard-pro|g' /etc/systemd/system/containerguard-dashboard.service
sudo systemctl daemon-reload
sudo systemctl restart containerguard
sudo systemctl restart containerguard-dashboard
Dashboard Shows "No actions recorded"
Solution:
# Check if history file exists
cat /tmp/containerguard_history.json

# If empty, restart the agent
sudo systemctl restart containerguard

# Wait 60 seconds and check again
sleep 60
cat /tmp/containerguard_history.json
Docker Connection Failed
Solution:
# Check Docker API access
curl http://192.168.217.165:2375/version

# Check hosts.conf
cat /etc/containerguard/hosts.conf

# Verify Docker is listening on the worker
ssh ruser@192.168.217.165 "sudo netstat -tlnp | grep 2375"
📁 Persistent History
History is stored in /tmp/containerguard_history.json:
[
  {
    "timestamp": "2026-09-09T05:35:57.986681",
    "action": "restart",
    "container": "test-postgres",
    "status": "success"
  }
]
📦 Uninstallation

# Stop and disable services
sudo systemctl stop containerguard
sudo systemctl stop containerguard-dashboard
sudo systemctl disable containerguard
sudo systemctl disable containerguard-dashboard

# Remove service files
sudo rm /etc/systemd/system/containerguard.service
sudo rm /etc/systemd/system/containerguard-dashboard.service
sudo systemctl daemon-reload

# Remove installation directory
rm -rf /home/ruser/containerguard-pro

# Remove logs
sudo rm -f /var/log/containerguard*.log

# Remove license and config (optional)
sudo rm -rf /etc/containerguard
📚 Next Steps
□ Configure Multi-Host monitoring
□ Set up Slack alerts
□ Customize monitoring rules
□ Scale to additional Docker hosts
🆘 Need Help?
GitHub Issues: https://github.com/muralipala1504/containerguard-pro/issues

Discussions: https://github.com/muralipala1504/containerguard-pro/discussions


