# 🔐 ContainerGuard Pro

**Autonomous Docker Agent** - Monitors containers and performs auto-healing, cleanup, and scaling across multiple hosts without human intervention.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

---

## 📖 Overview

ContainerGuard Pro is a lightweight, autonomous agent that monitors Docker containers across multiple hosts and automatically takes corrective actions. It acts as your personal **sysadmin**, handling common container failures without human intervention.

### 🚀 Key Features

| Feature | Description |
|---------|-------------|
| 🔍 **Multi-Host Monitoring** | Monitor multiple Docker hosts from one dashboard |
| 🔄 **Auto-Heal** | Automatically restarts crashed/exited containers |
| 🧹 **Auto-Cleanup** | Removes unused images, volumes, and dangling resources |
| 📊 **Web Dashboard** | Gradio-based UI with container status and action history |
| 📜 **Persistent History** | All actions logged to JSON file for audit |
| 🔔 **Slack Alerts** | Real-time notifications for container events |
| 🐳 **Docker Native** | Works with Docker and Docker Compose |
| 🔒 **SELinux Ready** | Automatically configures SELinux contexts |
| 🔐 **GitHub OAuth** | Enterprise-ready authentication |

---

## 💎 Pro vs Free

| Feature | Free | Pro |
|---------|------|-----|
| Container monitoring | ✅ Unlimited | ✅ Unlimited |
| Auto-restart | ✅ | ✅ |
| Web dashboard | ✅ | ✅ |
| **Action history** | 7 days | ✅ **Unlimited** |
| **Slack alerts** | ❌ | ✅ |
| **Auto-cleanup** | ❌ | ✅ |
| **Multi-Host** | ❌ | ✅ |
| **GitHub OAuth** | ❌ | ✅ |

---

## 🏗️ Architecture
┌─────────────────────────────────────────────────────────────────────────┐
│ ContainerGuard Pro System │
│ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Web Dashboard (Gradio) │ │
│ │ http://<ip>:7860 │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ │ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Agent Core (Python) │ │
│ │ ┌────────────┐ ┌────────────┐ ┌────────────┐ │ │
│ │ │ Scheduler │→ │ Decision │→ │ Action │ │ │
│ │ │ (30s) │ │ Engine │ │ Executor │ │ │
│ │ └────────────┘ └────────────┘ └────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ │ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Multi-Host Support │ │
│ │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │ │
│ │ │ vm1-agent │ │ vm2-worker │ │ vm3-worker │ │ │
│ │ │ (local) │ │ (remote) │ │ (remote) │ │ │
│ │ └──────────────┘ └──────────────┘ └──────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────┐
│ Docker Engines │
│ (Multiple Hosts) │
└─────────────────────┘


---

## ⚡ Quick Start

### One-Line Installation (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/muralipala1504/containerguard-pro/main/install.sh | bash
What Happens Automatically
The installer will:

✅ Clone the repository

✅ Create a Python virtual environment

✅ Install all dependencies

✅ Configure SELinux (if enforcing)

✅ Set up the agent as a systemd service

✅ Open firewall port 7860

✅ Start the web dashboard

🖥️ Manual Installation
Prerequisites
Component	Version
OS	AlmaLinux 8+, Ubuntu 20.04+, RHEL 8+
Docker	20.10+
Python	3.9+
CPU	2 cores
RAM	2 GB
Steps

# Clone the repository
git clone https://github.com/muralipala1504/containerguard-pro.git
cd containerguard-pro

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy service files
sudo cp deploy/containerguard.service /etc/systemd/system/
sudo cp deploy/containerguard-dashboard.service /etc/systemd/system/

# Apply SELinux context (if enforcing)
sudo chcon -R -t bin_t venv/bin/
sudo chcon -t bin_t agent/run-pro.sh
sudo chcon -t bin_t dashboard/run.sh

# Start services
sudo systemctl daemon-reload
sudo systemctl enable --now containerguard
sudo systemctl enable --now containerguard-dashboard

🌐 Dashboard
Access the web dashboard at http://<your-ip>:7860:

Container Status: Real-time view of all containers across all hosts

Action History: Persistent audit log of all actions

Manual Controls: Restart/stop containers manually

Multi-Host View: See all hosts and their containers

🔗 Multi-Host Configuration
Monitor multiple Docker hosts from one dashboard:

sudo mkdir -p /etc/containerguard
sudo tee /etc/containerguard/hosts.conf << 'EOF'
{
  "hosts": [
    {"name": "vm1-agent", "host": "unix:///var/run/docker.sock"},
    {"name": "vm2-worker", "host": "tcp://192.168.217.165:2375"},
    {"name": "vm3-worker", "host": "tcp://192.168.217.166:2375"}
  ]
}
EOF

sudo systemctl restart containerguard

🔐 Pro License Configuration
Activate Pro Features

sudo mkdir -p /etc/containerguard
sudo tee /etc/containerguard/license.json << 'EOF'
{
  "tier": "pro",
  "issued_at": "2026-09-09",
  "expires_at": "2027-09-09"
}
EOF

sudo systemctl restart containerguard
Slack Alerts (Pro)
Get a Slack webhook URL:

Go to https://api.slack.com/apps

Create a new app or use existing

Enable Incoming Webhooks

Copy the webhook URL

Add to .env file:

echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL" >> /home/ruser/containerguard-pro/.env

Restart the service:

sudo systemctl restart containerguard

⚠️ Security Note: Never commit .env files to GitHub! The repository already has .env in .gitignore.

🐳 Docker Installation
Using Docker Compose

# Clone and run
git clone https://github.com/muralipala1504/containerguard-pro.git
cd containerguard-pro
docker compose up -d

# Check status
docker compose ps

# Access dashboard
http://localhost:7860

Remote Docker Monitoring
If your containers run on a separate VM, set DOCKER_HOST:

environment:
  - DOCKER_HOST=tcp://<worker-ip>:2375

📁 Persistent History
All agent actions are logged to /tmp/containerguard_history.json:

[
  {
    "timestamp": "2026-09-09T05:35:57.986681",
    "action": "restart",
    "container": "test-postgres",
    "status": "success"
  }
]

🔧 Systemd Service Management

# Check status
sudo systemctl status containerguard
sudo systemctl status containerguard-dashboard

# View logs
sudo journalctl -u containerguard -f
sudo journalctl -u containerguard-dashboard -f

# Stop/Start/Restart
sudo systemctl {stop|start|restart} containerguard
sudo systemctl {stop|start|restart} containerguard-dashboard

# Enable on boot
sudo systemctl enable containerguard
sudo systemctl enable containerguard-dashboard

📝 Action History Export
Export audit logs from the dashboard:

CSV: Download as comma-separated values

JSON: Download as JSON format

🔐 GitHub OAuth (B2B)
Setup GitHub OAuth
Create a GitHub OAuth app at https://github.com/settings/applications/new

Set Authorization callback URL to http://your-ip:7861/oauth2/callback

Configure environment variables:

export GITHUB_CLIENT_ID=your_client_id
export GITHUB_CLIENT_SECRET=your_client_secret

Start Auth Server

cd /home/ruser/containerguard-pro
source venv/bin/activate
python auth.py

Access
Auth Server: http://your-ip:7861

Dashboard: http://your-ip:7860 (after login)

🤝 Contributing
Fork the repository

Create your feature branch (git checkout -b feature/amazing)

Commit your changes (git commit -m 'Add amazing feature')

Push to the branch (git push origin feature/amazing)

Open a Pull Request

📄 License
MIT License - see LICENSE for details

📞 Support
Issues: GitHub Issues

Discussions: GitHub Discussions

Documentation: INSTALL.md, ARCHITECTURE.md, API.md

Built with ❤️ for the Docker community


