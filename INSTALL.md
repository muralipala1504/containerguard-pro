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
```

### What the Installer Does

The installer will:

- ✅ Check prerequisites (Docker, Python, OS)
- ✅ Auto-install Docker if missing
- ✅ Clone the repository
- ✅ Create Python virtual environment
- ✅ Install dependencies (including OAuth packages)
- ✅ Configure SELinux context (if enforcing) — applies contexts to venv and wrapper scripts
- ✅ Create log files with proper permissions
- ✅ Prompt for Multi-Host configuration (local only or remote worker)
- ✅ Test connection to remote worker (if configured)
- ✅ Generate `/etc/containerguard/hosts.conf`
- ✅ Install systemd services (`containerguard-pro` + `containerguard-dashboard`)
- ✅ Open firewall port 7860
- ✅ Start the agent and dashboard services

After installation, you can optionally configure:
- Pro license: `/etc/containerguard/license.json`
- Slack alerts: `SLACK_WEBHOOK_URL` in `.env`
- GitHub OAuth: `GITHUB_CLIENT_ID` + `GITHUB_CLIENT_SECRET` in `.env`

---

## 📦 Manual Installation (Advanced)

### 1. Clone the Repository

```bash
cd ~
git clone https://github.com/muralipala1504/containerguard-pro.git
cd containerguard-pro
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate

# Verify Python path
which python
# Should show: /home/<username>/containerguard-pro/venv/bin/python
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import docker; print('✅ Docker SDK installed')"
python -c "import gradio; print('✅ Gradio installed')"
```

### 4. Configure SELinux (if enabled)

⚠️ **Critical Step for AlmaLinux/RHEL:**

```bash
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
```

### 5. Configure Docker Connection

**Option A: Local Docker (Same Machine)**

```bash
# Use default Docker socket
export DOCKER_HOST=unix:///var/run/docker.sock
```

**Option B: Remote Docker (Different Machine)**

On the **worker VM** (where containers run):

```bash
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
```

On the **control VM** (where ContainerGuard runs):

```bash
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
```

### 6. Configure Pro License (Optional)

```bash
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
```

### 7. Set Up as Systemd Services

**Step 1: Copy service files**

```bash
sudo cp deploy/containerguard-pro.service /etc/systemd/system/containerguard-pro.service
sudo cp deploy/containerguard-dashboard.service /etc/systemd/system/containerguard-dashboard.service
```

**Step 2: Replace INSTALL_USER placeholder with actual user**

```bash
sudo sed -i "s/\$INSTALL_USER/$USER/g" /etc/systemd/system/containerguard-pro.service
sudo sed -i "s/\$INSTALL_USER/$USER/g" /etc/systemd/system/containerguard-dashboard.service
```

**Step 3: Reload and start services**

```bash
sudo systemctl daemon-reload
sudo systemctl enable containerguard-pro
sudo systemctl enable containerguard-dashboard
sudo systemctl start containerguard-pro
sudo systemctl start containerguard-dashboard
```

**Step 4: Verify services**

```bash
sudo systemctl status containerguard-pro
sudo systemctl status containerguard-dashboard
```

### 8. Configure Slack Alerts (Pro)

⚠️ **Security Note:** Never commit Slack webhook URLs to GitHub!

```bash
# Add webhook to .env file (never commit this!)
echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL" >> ~/containerguard-pro/.env

# Restart service
sudo systemctl restart containerguard-pro
```

### 9. Open Firewall Port

```bash
# Firewalld
sudo firewall-cmd --add-port=7860/tcp --permanent
sudo firewall-cmd --reload

# UFW
sudo ufw allow 7860/tcp

# Verify
sudo firewall-cmd --list-ports
```

---

## 🔧 Wrapper Scripts Explained

ContainerGuard Pro uses wrapper scripts to handle SELinux and environment variables:

### Agent Wrapper (`agent/run-pro.sh`)

```bash
#!/bin/bash
export PYTHONPATH="$HOME/containerguard-pro:$PYTHONPATH"
cd $HOME/containerguard-pro
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi
source venv/bin/activate
exec python agent/runner.py
```

### Dashboard Wrapper (`dashboard/run.sh`)

```bash
#!/bin/bash
cd $HOME/containerguard-pro
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi
source venv/bin/activate
python dashboard/app.py
```

---

## 🌐 Dashboard Access

```bash
# Access the dashboard
http://<your-ip>:7860

# Check if dashboard is running
sudo systemctl status containerguard-dashboard

# View dashboard logs
sudo journalctl -u containerguard-dashboard -f
```

---

## 🔍 Verification

### Verify Agent is Running

```bash
# Check service status
sudo systemctl status containerguard-pro

# Check logs
sudo tail -20 /var/log/containerguard-pro.log
```

Expected output:

```
2026-09-11 11:25:53,482 - INFO - ✅ local-test on vm2-worker: RUNNING
2026-09-11 11:25:53,482 - INFO - ✅ test-app on vm2-worker: RUNNING
2026-09-11 11:25:53,483 - INFO - 📊 Monitored containers across 2 hosts, restarted 0
2026-09-11 11:25:53,483 - INFO - ✅ Monitoring cycle completed
```

### Verify Pro Features

```bash
# Check if Pro features are enabled
sudo grep -i "pro" /var/log/containerguard-pro.log | tail -5

# Check license
python -c "import json; f=open('/etc/containerguard/license.json'); print(json.load(f))"
```

### Verify Multi-Host

```bash
sudo cat /etc/containerguard/hosts.conf
sudo tail -20 /var/log/containerguard-pro.log | grep -i "connected\|host"
```

---

## 🐛 Common Issues & Solutions

### SELinux Blocking Execution

**Symptoms:** Service fails with `status=203/EXEC` or `Permission denied`

**Solution:**

```bash
# Apply SELinux context to venv binaries
sudo chcon -R -t bin_t $HOME/containerguard-pro/venv/bin/

# Apply to wrapper scripts
sudo chcon -t bin_t $HOME/containerguard-pro/agent/run-pro.sh
sudo chcon -t bin_t $HOME/containerguard-pro/dashboard/run.sh

# Restart services
sudo systemctl restart containerguard-pro
sudo systemctl restart containerguard-dashboard
```

### Service Fails to Start

**Symptoms:** Service shows errors about missing files or paths

**Solution:**

```bash
# Check the actual error
sudo journalctl -u containerguard-pro -n 20 --no-pager

# Verify service file is correct
cat /etc/systemd/system/containerguard-pro.service | grep -E "User|Group|WorkingDirectory|ExecStart"

# Restart services
sudo systemctl daemon-reload
sudo systemctl restart containerguard-pro
sudo systemctl restart containerguard-dashboard
```

### Dashboard Shows "No actions recorded"

**Solution:**

```bash
# Check if history file exists
cat /tmp/containerguard_history.json

# If empty, restart the agent
sudo systemctl restart containerguard-pro

# Wait 60 seconds and check again
sleep 60
cat /tmp/containerguard_history.json
```

### Docker Connection Failed

**Solution:**

```bash
# Check Docker API access
curl http://192.168.217.165:2375/version

# Check hosts.conf
cat /etc/containerguard/hosts.conf

# Verify Docker is listening on the worker
ssh ruser@<worker-ip> "sudo netstat -tlnp | grep 2375"
```

### Gradio Import Error (HfFolder)

**Symptoms:** `ImportError: cannot import name 'HfFolder' from 'huggingface_hub'`

**Solution:**

```bash
cd $HOME/containerguard-pro && source venv/bin/activate
pip install gradio==4.44.1 huggingface-hub==0.23.4
sudo systemctl restart containerguard-dashboard
```

---

## 📁 Persistent History & Audit Logs

ContainerGuard Pro maintains two log files:

**1. Audit Log** — `/tmp/containerguard_audit.json`

Records all actions (auto-heal, manual restart, cleanup) for compliance:

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

**2. Action History** — `/tmp/containerguard_history.json`

Tracks container-level actions with host information:

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

---

## 📦 Uninstallation

```bash
# Stop and disable services
sudo systemctl stop containerguard-pro
sudo systemctl stop containerguard-dashboard
sudo systemctl disable containerguard-pro
sudo systemctl disable containerguard-dashboard

# Remove service files
sudo rm /etc/systemd/system/containerguard-pro.service
sudo rm /etc/systemd/system/containerguard-dashboard.service
sudo systemctl daemon-reload

# Remove installation directory
rm -rf $HOME/containerguard-pro

# Remove logs
sudo rm -f /var/log/containerguard*.log

# Remove license and config (optional)
sudo rm -rf /etc/containerguard
```

---

## 📚 Next Steps

- [ ] Configure Multi-Host monitoring
- [ ] Set up Slack alerts
- [ ] Customize monitoring rules
- [ ] Scale to additional Docker hosts

---

## 🆘 Need Help?

- **GitHub Issues**: https://github.com/muralipala1504/containerguard-pro/issues
- **Discussions**: https://github.com/muralipala1504/containerguard-pro/discussions
