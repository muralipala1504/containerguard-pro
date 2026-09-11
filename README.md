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

ContainerGuard Pro runs as two systemd services on a control node:

| Component | Port | Purpose |
|-----------|------|---------|
| **Agent** | — | Monitors Docker hosts, auto-heals containers |
| **Dashboard** | 7860 | Gradio web UI for monitoring and control |
| **Auth Server** (optional) | 7861 | GitHub OAuth login |

### High-Level Flow

```

Control Node (vm1-agent)                    Worker Nodes
┌──────────────────────┐                    ┌─────────────────┐
│  Dashboard :7860     │                    │  VM2 :2375      │
│  Agent (monitor)     │ ─── Docker API ──▶ │  VM3 :2375      │
│  /etc/containerguard/│                    │  (containers)   │
│    ├── hosts.conf    │                    └─────────────────┘
│    ├── license.json  │
│    └── .env          │
└──────────────────────┘
```


> **📖 For detailed architecture, data flow, and design decisions, see [ARCHITECTURE.md](ARCHITECTURE.md).**

## ⚡ Quick Start

### One-Line Installation (Recommended)

```bash

curl -sSL https://raw.githubusercontent.com/muralipala1504/containerguard-pro/main/install.sh | bash
```

### What Happens Automatically

The installer will:

- ✅ Check prerequisites (Docker, Python, OS)
- ✅ Auto-install Docker if missing
- ✅ Clone the repository
- ✅ Create Python virtual environment
- ✅ Install all dependencies (including OAuth packages)
- ✅ Configure SELinux (if enforcing) — applies contexts to venv and wrapper scripts
- ✅ Create log files with proper permissions
- ✅ Prompt for Multi-Host configuration (optional)
- ✅ Generate `/etc/containerguard/hosts.conf`
- ✅ Install systemd services (agent + dashboard)
- ✅ Open firewall port 7860
- ✅ Start the agent and dashboard services

After installation, you can optionally configure:
- Pro license: `/etc/containerguard/license.json`
- Slack alerts: `SLACK_WEBHOOK_URL` in `.env`
- GitHub OAuth: `GITHUB_CLIENT_ID` + `GITHUB_CLIENT_SECRET` in `.env`

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
sudo cp deploy/containerguard-pro.service /etc/systemd/system/containerguard-pro.service
sudo cp deploy/containerguard-dashboard.service /etc/systemd/system/containerguard-dashboard.service

# Replace INSTALL_USER placeholder with actual user
sudo sed -i "s/\$INSTALL_USER/$USER/g" /etc/systemd/system/containerguard-pro.service
sudo sed -i "s/\$INSTALL_USER/$USER/g" /etc/systemd/system/containerguard-dashboard.service

# Apply SELinux context (if enforcing)
sudo chcon -R -t bin_t venv/bin/
sudo chcon -t bin_t agent/run-pro.sh
sudo chcon -t bin_t dashboard/run.sh

# Start services
sudo systemctl daemon-reload
sudo systemctl enable --now containerguard-pro
sudo systemctl enable --now containerguard-dashboard

🌐 Dashboard
Access the web dashboard at http://<your-ip>:7860:

Container Status: Real-time view of all containers across all hosts

Action History: Persistent audit log of all actions

Manual Controls: Restart/stop containers manually

Multi-Host View: See all hosts and their containers

🔗 Multi-Host Configuration

ContainerGuard Pro can monitor multiple Docker hosts from a single dashboard.

### Option 1: During Installation (Recommended)

The installer will prompt you:

```

Do you want to monitor a remote Docker host? (Multi-Host mode)
  1) Yes - configure remote worker now
  2) No - local Docker only (can configure later)
Choose option (1-2): 1
Enter remote host name (e.g., vm2-worker): VM2
Enter remote Docker IP (e.g., 192.168.217.165): 192.168.217.170
[SUCCESS] ✅ Connected to VM2
```


The installer automatically:
- Tests the connection to the remote host
- Generates `/etc/containerguard/hosts.conf`
- Restarts services with the new configuration

### Option 2: Manual Configuration

Edit `/etc/containerguard/hosts.conf`:

```bash
sudo tee /etc/containerguard/hosts.conf << 'EOF'
{
  "hosts": [
    {"name": "local", "host": "unix:///var/run/docker.sock"},
    {"name": "vm2-worker", "host": "tcp://192.168.217.165:2375"},
    {"name": "vm3-worker", "host": "tcp://192.168.217.166:2375"}
  ]
}
EOF

sudo systemctl restart containerguard-pro
```


### Prerequisites on Worker Nodes

On each worker node, expose the Docker API:

```bash
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo tee /etc/systemd/system/docker.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0:2375
EOF

sudo systemctl daemon-reload
sudo systemctl restart docker
sudo firewall-cmd --add-port=2375/tcp --permanent
sudo firewall-cmd --reload
```

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

echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL" >> ~/containerguard-pro/.env

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

📁 Persistent History & Audit Logs

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

🔧 Systemd Service Management
# Check status
sudo systemctl status containerguard-pro
sudo systemctl status containerguard-dashboard

# View logs
sudo journalctl -u containerguard-pro -f
sudo journalctl -u containerguard-dashboard -f

# Stop/Start/Restart
sudo systemctl {stop|start|restart} containerguard-pro
sudo systemctl {stop|start|restart} containerguard-dashboard

# Enable on boot
sudo systemctl enable containerguard-pro
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

cd ~/containerguard-pro
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


