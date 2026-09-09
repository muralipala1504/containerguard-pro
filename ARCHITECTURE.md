# 🏗️ ContainerGuard Pro Architecture

Technical design and data flow documentation for ContainerGuard Pro.

---

## 📋 Overview

ContainerGuard Pro is a lightweight, autonomous Docker monitoring and healing agent built with Python. It operates as a systemd service, continuously monitoring containers across multiple hosts and taking corrective actions when issues are detected.

---

## 🎯 Core Components
┌─────────────────────────────────────────────────────────────────────────────┐
│ ContainerGuard Pro System │
├─────────────────────────────────────────────────────────────────────────────┤
│ │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ User Interface Layer │ │
│ │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │ │
│ │ │ Gradio │ │ CLI Commands │ │ REST API │ │ │
│ │ │ Dashboard │ │ (Manual) │ │ (Future) │ │ │
│ │ │ Port: 7860 │ │ │ │ │ │ │
│ │ └─────────────────┘ └─────────────────┘ └─────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│ │ │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ Agent Core Layer │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│ │ │ Scheduler │→ │ Decision │→ │ Action │ │ │
│ │ │ (Timer) │ │ Engine │ │ Executor │ │ │
│ │ │ 30s interval│ │ (Rules) │ │ (Docker) │ │ │
│ │ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│ │ │ │
│ │ ┌─────────────────────────────────────────────────────────────┐ │ │
│ │ │ Persistent History (JSON) │ │ │
│ │ │ /tmp/containerguard_history.json │ │ │
│ │ │ - All agent actions │ │ │
│ │ │ - Timestamps │ │ │
│ │ │ - Success/failure status │ │ │
│ │ └─────────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│ │ │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ Integration Layer │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│ │ │ Docker │ │ Slack │ │ Systemd │ │ │
│ │ │ SDK │ │ Alerts │ │ Service │ │ │
│ │ │ (Multi-Host)│ │ (Pro) │ │ (Daemon) │ │ │
│ │ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────┐
│ Multiple Docker Engines │
│ (Local + Remote Hosts) │
└─────────────────────────────┘


---

## 📂 Project Structure
containerguard-pro/
├── agent/
│ ├── actions.py # Core action execution (restart, cleanup)
│ ├── core.py # Main agent engine
│ ├── runner.py # Entry point for systemd service
│ ├── run-pro.sh # Wrapper script with SELinux and env setup
│ └── init.py
├── dashboard/
│ ├── app.py # Gradio web dashboard
│ ├── auth_dashboard.py # GitHub OAuth integration
│ └── run.sh # Dashboard wrapper script
├── deploy/
│ ├── containerguard.service # Systemd service for agent
│ └── containerguard-dashboard.service # Systemd service for dashboard
├── pro_agent/
│ ├── slack.py # Slack alert integration
│ └── cleanup.py # Auto-cleanup functionality
├── license/
│ └── check.py # License validation
├── install.sh # One-line installer
├── requirements.txt # Python dependencies
└── .env # Environment variables (never commit!)


---

## 🐳 Multi-Host Architecture

ContainerGuard Pro supports monitoring multiple Docker hosts simultaneously through a centralized configuration file.

### Configuration File (`/etc/containerguard/hosts.conf`)

```json
{
  "hosts": [
    {"name": "vm1-agent", "host": "unix:///var/run/docker.sock"},
    {"name": "vm2-worker", "host": "tcp://192.168.217.165:2375"},
    {"name": "vm3-worker", "host": "tcp://192.168.217.166:2375"}
  ]
}
Multi-Host Data Flow

┌─────────────────────────────────────────────────────────────────┐
│                    ContainerGuard Agent                        │
│                                                                 │
│  1. Read /etc/containerguard/hosts.conf                        │
│  2. Connect to each Docker host                                │
│  3. Monitor all containers across all hosts                    │
│  4. Aggregate results in one dashboard                         │
└─────────────────────────────────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
┌─────────────────┐┌─────────────────┐┌─────────────────┐
│  vm1-agent      ││  vm2-worker     ││  vm3-worker     │
│  (local)        ││  (remote)       ││  (remote)       │
│  unix://...     ││  tcp://...:2375 ││  tcp://...:2375 │
├─────────────────┤├─────────────────┤├─────────────────┤
│  • Container A  ││  • Container X  ││  • Container M  │
│  • Container B  ││  • Container Y  ││  • Container N  │
│  • Container C  ││  • Container Z  ││  • Container O  │
└─────────────────┘└─────────────────┘└─────────────────┘

🔐 SELinux Integration
ContainerGuard Pro is fully compatible with SELinux-enforcing systems (AlmaLinux, RHEL).

SELinux Context Requirements
File/Directory	Context	Command
venv/bin/*	bin_t	sudo chcon -R -t bin_t venv/bin/
agent/run-pro.sh	bin_t	sudo chcon -t bin_t agent/run-pro.sh
dashboard/run.sh	bin_t	sudo chcon -t bin_t dashboard/run.sh
Why Wrapper Scripts?
Systemd services running on SELinux-enforcing systems need proper context. The wrapper scripts:

Source environment variables (.env file)

Activate the virtual environment

Execute the Python scripts with correct SELinux context

┌─────────────────────────────────────────────────────────────────┐
│                  Systemd Service Flow                          │
│                                                                 │
│  systemd → run-pro.sh → source .env → venv/bin/python → runner.py
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  run-pro.sh (Wrapper)                                  │   │
│  │  - Sets PYTHONPATH                                     │   │
│  │  - Loads .env variables                                │   │
│  │  - Activates venv                                      │   │
│  │  - Executes python agent/runner.py                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

🔄 Data Flow
1. Agent Monitoring Cycle

┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Cycle (30s)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐                                               │
│  │  Timer      │  → Triggered every 30 seconds                │
│  └─────────────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                               │
│  │  Connect to │  → Read /etc/containerguard/hosts.conf       │
│  │  Docker     │  → Connect to each host                       │
│  └─────────────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                               │
│  │  Check      │  → List all containers                        │
│  │  Containers │  → Check status (RUNNING/EXITED/PAUSED)      │
│  └─────────────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Decision Engine                                        │   │
│  │  - EXITED → Auto-heal (restart)                        │   │
│  │  - FAILED → Log error                                  │   │
│  │  - RUNNING → Continue monitoring                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                               │
│  │  Log Action │  → Write to /tmp/containerguard_history.json │
│  │  to History │  → Send Slack alert (if Pro enabled)         │
│  └─────────────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                               │
│  │  Wait 30s   │  → Repeat cycle                              │
│  └─────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘

2. Dashboard Data Flow

┌─────────────────────────────────────────────────────────────────┐
│                    Dashboard Data Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User → Browser → http://<ip>:7860                            │
│                    │                                            │
│                    ▼                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Gradio Dashboard (app.py)                              │   │
│  │  - Reads /tmp/containerguard_history.json              │   │
│  │  - Fetches live container status from Docker           │   │
│  │  - Displays unified view of all hosts                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                    │                                            │
│                    ▼                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  History File (JSON)                                    │   │
│  │  /tmp/containerguard_history.json                      │   │
│  │  - Auto-heal actions                                    │   │
│  │  - Manual restarts                                      │   │
│  │  - Cleanup operations                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

💎 Pro Features Architecture
License Validation
┌─────────────────────────────────────────────────────────────────┐
│                    License Check Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Agent starts                                               │
│  2. Read /etc/containerguard/license.json                     │
│  3. Validate tier (pro/free)                                  │
│  4. Check expiration date                                     │
│  5. Enable/disable Pro features                               │
└─────────────────────────────────────────────────────────────────┘

Slack Alerts (Pro)

┌─────────────────────────────────────────────────────────────────┐
│                    Slack Alert Flow                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Container restarted/error detected                         │
│  2. Check if Pro license active                                │
│  3. Check if SLACK_WEBHOOK_URL configured                      │
│  4. Send POST request to Slack webhook                         │
│  5. Log success/failure to agent log                           │
└─────────────────────────────────────────────────────────────────┘

Auto-Cleanup (Pro)

┌─────────────────────────────────────────────────────────────────┐
│                    Auto-Cleanup Flow                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Scheduled trigger (configurable)                           │
│  2. Check Pro license active                                   │
│  3. Remove unused images                                       │
│  4. Remove dangling volumes                                    │
│  5. Remove build cache                                         │
│  6. Log cleanup results                                        │
└─────────────────────────────────────────────────────────────────┘

🔧 Service Management
Systemd Service Configuration
Agent Service (/etc/systemd/system/containerguard.service):

[Unit]
Description=ContainerGuard Agent - Autonomous Docker Monitoring
After=docker.service network.target
Wants=docker.service

[Service]
Type=simple
User=ruser
Group=ruser
WorkingDirectory=/home/ruser/containerguard-pro
Environment="PATH=/home/ruser/containerguard-pro/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ruser/containerguard-pro/agent/run-pro.sh
Restart=always
RestartSec=10
StandardOutput=append:/var/log/containerguard.log
StandardError=append:/var/log/containerguard-error.log

[Install]
WantedBy=multi-user.target

Dashboard Service (/etc/systemd/system/containerguard-dashboard.service):

[Unit]
Description=ContainerGuard Dashboard
After=network.target containerguard.service
Wants=containerguard.service

[Service]
Type=simple
User=ruser
Group=ruser
WorkingDirectory=/home/ruser/containerguard-pro
Environment="PATH=/home/ruser/containerguard-pro/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ruser/containerguard-pro/dashboard/run.sh
Restart=always
RestartSec=10
StandardOutput=append:/var/log/containerguard-dashboard.log
StandardError=append:/var/log/containerguard-dashboard-error.log

[Install]
WantedBy=multi-user.target

📊 Data Persistence

History File Schema (/tmp/containerguard_history.json)

{
  "history": [
    {
      "timestamp": "2026-09-09T05:35:57.986681",
      "action": "restart",
      "container": "test-postgres",
      "host": "vm2-worker",
      "status": "success",
      "details": "Container restarted successfully"
    }
  ]
}

Audit Log Schema (/tmp/containerguard_audit.json)

{
  "audit": [
    {
      "timestamp": "2026-09-09T05:35:57.986681",
      "user": "user",
      "action": "restart",
      "resource": "test-nginx",
      "status": "success",
      "source": "web-dashboard"
    }
  ]
}

🔒 Security Considerations
.env files never committed - Added to .gitignore

SELinux enforcement - Proper contexts applied

User separation - Services run as ruser, not root

Multi-Host authentication - Use TLS for remote Docker connections

Slack webhooks - Stored in .env, not in code

📈 Performance Characteristics
Metric	Value
Memory Usage	~15-20 MB per agent
CPU Usage	~1-2% during monitoring
API Calls	1 per host per 30s
Log Size	~50 MB/day (rotated)
History File	~1 MB per 1000 actions
🧪 Testing Architecture

┌─────────────────────────────────────────────────────────────────┐
│                    Test Environment                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  vm1-agent (Control)                                   │   │
│  │  - ContainerGuard Pro installed                        │   │
│  │  - Agent service running                               │   │
│  │  - Dashboard accessible on port 7860                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                    │                                            │
│                    │ Docker API (port 2375)                     │
│                    ▼                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  vm2-worker (Worker)                                   │   │
│  │  - Test containers running                              │   │
│  │  - Docker API exposed on port 2375                     │   │
│  │  - Monitor by ContainerGuard                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

🚀 Deployment Options
Method	Command	Best For
VM (install.sh)	curl ... | bash	Production VMs, systemd integration
Docker Compose	docker compose up -d	Container environments, quick testing
Manual	Step-by-step install	Custom configurations, debugging


