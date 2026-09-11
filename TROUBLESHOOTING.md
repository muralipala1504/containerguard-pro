# 🐛 ContainerGuard Pro Troubleshooting Guide

Common issues and their solutions, based on real production experience.

---

## 📋 Table of Contents

1. [Installation Issues](#installation-issues)
2. [SELinux Issues](#selinux-issues)
3. [Service Startup Issues](#service-startup-issues)
4. [Dashboard Issues](#dashboard-issues)
5. [Multi-Host Issues](#multi-host-issues)
6. [Pro Features Issues](#pro-features-issues)
7. [Slack Alert Issues](#slack-alert-issues)
8. [Logging Issues](#logging-issues)
9. [Quick Diagnostic Commands](#quick-diagnostic-commands)

---

## Installation Issues

### Issue: Installer fails with "Docker is not installed"

**Cause:** Docker isn't installed on the system.

**Solution:**
The installer auto-installs Docker if missing. If it still fails:

```bash
# Manually install Docker (AlmaLinux/RHEL)
sudo dnf install -y dnf-utils
sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io
sudo systemctl enable --now docker

# Or Ubuntu/Debian
sudo apt update && sudo apt install -y docker.io
```

---

### Issue: Installer fails with "Directory exists"

**Cause:** A previous installation exists.

**Solution:**
Either confirm removal when prompted, or manually remove:

```bash
rm -rf ~/containerguard-pro
```

---

### Issue: Git clone fails (SSL/TLS error)

**Cause:** Network issues or missing CA certificates.

**Solution:**

```bash
# Update CA certificates
sudo dnf install -y ca-certificates  # AlmaLinux
sudo apt install -y ca-certificates  # Ubuntu

# Retry installation
curl -sSL https://raw.githubusercontent.com/muralipala1504/containerguard-pro/main/install.sh | bash
```

---

## SELinux Issues

### Issue: Service fails with `status=203/EXEC`

**Symptoms:**
```
Active: activating (auto-restart) (Result: exit-code)
Process: ExecStart=/home/user/containerguard-pro/agent/run-pro.sh (code=exited, status=203/EXEC)
```

**Cause:** SELinux blocks execution of wrapper scripts or venv binaries.

**Solution:**

```bash
# Check SELinux status
getenforce

# Apply correct context to venv binaries
sudo chcon -R -t bin_t ~/containerguard-pro/venv/bin/

# Apply context to wrapper scripts
sudo chcon -t bin_t ~/containerguard-pro/agent/run-pro.sh
sudo chcon -t bin_t ~/containerguard-pro/dashboard/run.sh

# Restart services
sudo systemctl restart containerguard-pro
sudo systemctl restart containerguard-dashboard
```

**Verify contexts:**

```bash
ls -Z ~/containerguard-pro/agent/run-pro.sh
# Expected: unconfined_u:object_r:bin_t:s0
```

---

### Issue: SELinux blocks the venv Python binary

**Symptom:** Service fails to start with permission denied even after chcon.

**Solution:**

```bash
# Apply context recursively to entire venv
sudo chcon -R -t bin_t ~/containerguard-pro/venv/

# If semanage is available, make it persistent
sudo semanage fcontext -a -t bin_t "$HOME/containerguard-pro/venv/bin(/.*)?"
sudo restorecon -Rv ~/containerguard-pro/venv/bin/
```

---

## Service Startup Issues

### Issue: Service fails with `status=217/USER`

**Symptom:**
```
Process: ExecStart=... (code=exited, status=217/USER)
```

**Cause:** The `User=` field in the service file contains an unexpanded variable or wrong username.

**Solution:**

```bash
# Check the service file
cat /etc/systemd/system/containerguard-pro.service | grep -E "User|Group"

# If it shows "User=$INSTALL_USER" (literal), replace with actual username
sudo sed -i "s/\$INSTALL_USER/$(whoami)/g" /etc/systemd/system/containerguard-pro.service
sudo sed -i "s/\$INSTALL_USER/$(whoami)/g" /etc/systemd/system/containerguard-dashboard.service

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart containerguard-pro
sudo systemctl restart containerguard-dashboard
```

---

### Issue: Service fails with `status=1/FAILURE` and no clear error

**Cause:** Python script crashes on startup (often log file permission).

**Solution:**

```bash
# Run the wrapper manually to see the real error
sudo -u $(whoami) ~/containerguard-pro/agent/run-pro.sh

# Common fix: create log files with proper permissions
sudo touch /var/log/containerguard-pro.log
sudo touch /var/log/containerguard-pro-error.log
sudo touch /var/log/containerguard-dashboard.log
sudo touch /var/log/containerguard-dashboard-error.log

sudo chown $(whoami):$(whoami) /var/log/containerguard-pro.log
sudo chown $(whoami):$(whoami) /var/log/containerguard-pro-error.log
sudo chown $(whoami):$(whoami) /var/log/containerguard-dashboard.log
sudo chown $(whoami):$(whoami) /var/log/containerguard-dashboard-error.log

sudo chmod 644 /var/log/containerguard-*.log
sudo systemctl restart containerguard-pro
sudo systemctl restart containerguard-dashboard
```

---

### Issue: Service points to wrong directory (`containerguard-new`)

**Symptom:** Logs show `containerguard-new` paths even though we installed `containerguard-pro`.

**Cause:** Old service file from previous installation.

**Solution:**

```bash
# Fix paths in service files
sudo sed -i 's|containerguard-new|containerguard-pro|g' /etc/systemd/system/containerguard-pro.service
sudo sed -i 's|containerguard-new|containerguard-pro|g' /etc/systemd/system/containerguard-dashboard.service

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart containerguard-pro
sudo systemctl restart containerguard-dashboard
```

---

## Dashboard Issues

### Issue: Dashboard fails with `ImportError: cannot import name 'HfFolder'`

**Symptom:**
```
ImportError: cannot import name 'HfFolder' from 'huggingface_hub'
```

**Cause:** Incompatible `gradio` and `huggingface-hub` versions.

**Solution:**

```bash
cd ~/containerguard-pro && source venv/bin/activate

# Uninstall and reinstall specific versions
pip uninstall -y gradio huggingface-hub
pip install gradio==4.44.1 huggingface-hub==0.23.4

# Restart dashboard
sudo systemctl restart containerguard-dashboard
```

---

### Issue: Dashboard not accessible on port 7860

**Symptom:** `curl: (7) Failed to connect to <ip> port 7860`

**Cause:** Firewall blocking or service not running.

**Solution:**

```bash
# Check if service is running
sudo systemctl status containerguard-dashboard

# Check if port is listening
sudo netstat -tlnp | grep 7860

# Open firewall
sudo firewall-cmd --add-port=7860/tcp --permanent
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-ports
```

---

### Issue: Dashboard shows "No actions recorded yet"

**Cause:** No actions have happened yet, OR audit log file is empty.

**Solution:**

```bash
# Check if audit file exists
cat /tmp/containerguard_audit.json

# If missing, trigger a test action
cd ~/containerguard-pro && source venv/bin/activate
python -c "
from audit import log_action
log_action('test-user', 'test', 'test-resource', 'Test action', 'success')
"

# Refresh dashboard
# You should see the test action
```

---

### Issue: Dashboard shows empty Nodes/Containers

**Cause:** No Docker hosts reachable, or hosts.conf is misconfigured.

**Solution:**

```bash
# Check hosts.conf
cat /etc/containerguard/hosts.conf

# Test each host
curl -s http://<worker-ip>:2375/version | head -3

# For local socket
docker ps

# Restart agent if needed
sudo systemctl restart containerguard-pro
```

---

## Multi-Host Issues

### Issue: vm2-worker shows as "Disconnected"

**Symptoms:**
```
❌ vm2-worker: Disconnected
```

**Cause:** Docker API not exposed, firewall blocking, or wrong IP.

**Solution:**

On the **worker VM**:

```bash
# 1. Verify Docker API is exposed
sudo netstat -tlnp | grep 2375

# If not listening, enable it:
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo tee /etc/systemd/system/docker.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0:2375
EOF

sudo systemctl daemon-reload
sudo systemctl restart docker

# 2. Open firewall
sudo firewall-cmd --add-port=2375/tcp --permanent
sudo firewall-cmd --reload

# 3. Verify from control node
# (Run this on control node)
curl http://<worker-ip>:2375/version
```

---

### Issue: Wrong IP in hosts.conf

**Symptom:** Agent can't connect to worker.

**Cause:** IP address in `hosts.conf` doesn't match actual worker IP.

**Solution:**

```bash
# Check worker's actual IP
# (Run on worker VM)
hostname -I

# Update hosts.conf on control node
sudo vi /etc/containerguard/hosts.conf

# Restart agent
sudo systemctl restart containerguard-pro

# Verify connection
sudo tail -20 /var/log/containerguard-pro.log | grep "connected"
```

---

### Issue: Auto-heal works on local but not on remote host

**Cause:** Remote Docker API requires permissions or is not reachable.

**Solution:**

```bash
# Test Docker API access from control node
curl http://<worker-ip>:2375/containers/json

# Test Python connection
cd ~/containerguard-pro && source venv/bin/activate
python -c "
import docker
client = docker.DockerClient(base_url='tcp://<worker-ip>:2375', timeout=5)
print(f'Connected: {client.version()[\"Version\"]}')
print(f'Containers: {len(client.containers.list(all=True))}')
"
```

---

## Pro Features Issues

### Issue: "Free tier: 7-day history limit, no Pro features"

**Cause:** License file is missing or invalid.

**Solution:**

```bash
# Check if license file exists
cat /etc/containerguard/license.json

# If missing, create it
sudo mkdir -p /etc/containerguard
sudo tee /etc/containerguard/license.json << 'EOF'
{
  "tier": "pro",
  "issued_at": "2026-09-09",
  "expires_at": "2027-09-09"
}
EOF

# Fix permissions
sudo chmod 644 /etc/containerguard/license.json
sudo chown $(whoami):$(whoami) /etc/containerguard/license.json

# Restart agent
sudo systemctl restart containerguard-pro

# Verify in logs
sudo grep -i "pro" /var/log/containerguard-pro.log | tail -5
# Should show: ✅ Pro features enabled: Slack alerts, Auto-cleanup
```

---

### Issue: Auto-cleanup not running

**Cause:** Pro license not active, or cleanup module not imported.

**Solution:**

```bash
# Check license
python -c "from license import check_license; print(f'Pro: {check_license()}')"

# Manual cleanup test
cd ~/containerguard-pro && source venv/bin/activate
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

## Slack Alert Issues

### Issue: No Slack alerts being sent

**Cause:** Webhook URL missing, invalid, or `.env` not loaded.

**Solution:**

```bash
# 1. Check .env file
cat ~/containerguard-pro/.env

# Should contain:
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# 2. Test webhook manually
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"🔔 Test from ContainerGuard"}' \
  https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Expected: "ok"

# 3. Check wrapper loads .env
cat ~/containerguard-pro/agent/run-pro.sh | grep "source .env"

# 4. Restart service
sudo systemctl restart containerguard-pro

# 5. Check logs for Slack activity
sudo grep -i "slack" /var/log/containerguard-pro.log | tail -5
```

---

### Issue: Slack webhook invalidated by Slack

**Symptom:**
```
Hi there, We recently invalidated an incoming webhook associated with...
```

**Cause:** Webhook URL was exposed publicly (e.g., committed to GitHub).

**Solution:**

1. **Remove webhook from repo:**
```bash
cd ~/containerguard-pro
sed -i '/SLACK_WEBHOOK_URL/d' .env
echo ".env" >> .gitignore
git rm --cached .env 2>/dev/null || true
git add .gitignore
git commit -m "Security: Remove exposed webhook"
git push origin main
```

2. **Get new webhook URL:**
   - Go to: https://api.slack.com/apps
   - Find your app → "Incoming Webhooks"
   - Generate new webhook URL

3. **Add to `.env`:**
```bash
echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/NEW/WEBHOOK/URL" >> ~/containerguard-pro/.env
sudo systemctl restart containerguard-pro
```

---

## Logging Issues

### Issue: `Permission denied: '/var/log/containerguard-pro.log'`

**Cause:** Log file doesn't exist, or wrong ownership.

**Solution:**

```bash
# Create log files
sudo touch /var/log/containerguard-pro.log
sudo touch /var/log/containerguard-pro-error.log
sudo touch /var/log/containerguard-dashboard.log
sudo touch /var/log/containerguard-dashboard-error.log

# Fix ownership
sudo chown $(whoami):$(whoami) /var/log/containerguard-*.log

# Fix permissions
sudo chmod 644 /var/log/containerguard-*.log

# Restart services
sudo systemctl restart containerguard-pro
sudo systemctl restart containerguard-dashboard
```

---

### Issue: Logs not rotating (disk filling up)

**Solution:**

```bash
# Create logrotate config
sudo tee /etc/logrotate.d/containerguard << 'EOF'
/var/log/containerguard*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 644 $(whoami) $(whoami)
}
EOF

# Test logrotate
sudo logrotate -d /etc/logrotate.d/containerguard
```

---

## Quick Diagnostic Commands

### Health Check (One-Liner)

```bash
echo "=== Services ===" && \
echo "Agent: $(systemctl is-active containerguard-pro)" && \
echo "Dashboard: $(systemctl is-active containerguard-dashboard)" && \
echo "" && \
echo "=== Config ===" && \
cat /etc/containerguard/hosts.conf && \
echo "" && \
echo "=== License ===" && \
cat /etc/containerguard/license.json && \
echo "" && \
echo "=== Logs (last 5) ===" && \
sudo tail -5 /var/log/containerguard-pro.log
```

### Check All Hosts

```bash
# List all hosts and their status
sudo tail -50 /var/log/containerguard-pro.log | grep -E "Connected|Disconnected|Found"
```

### Test Full System

```bash
# 1. Services
sudo systemctl status containerguard-pro --no-pager
sudo systemctl status containerguard-dashboard --no-pager

# 2. Docker hosts
cat /etc/containerguard/hosts.conf

# 3. Audit log
cat /tmp/containerguard_audit.json

# 4. Test Slack
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test"}' \
  $(grep SLACK_WEBHOOK_URL ~/containerguard-pro/.env | cut -d= -f2 | head -1)
```

---

## 🆘 Still Stuck?

If none of these solutions work:

1. **Collect diagnostics:**
```bash
{
  echo "=== OS ==="; cat /etc/os-release | head -3
  echo "=== Docker ==="; docker --version
  echo "=== Python ==="; python3 --version
  echo "=== SELinux ==="; getenforce
  echo "=== Services ==="; systemctl status containerguard-pro --no-pager; systemctl status containerguard-dashboard --no-pager
  echo "=== Logs ==="; sudo tail -50 /var/log/containerguard-pro.log
} > /tmp/containerguard-diagnostics.txt
```

2. **Open a GitHub issue:**
   - Go to: https://github.com/muralipala1504/containerguard-pro/issues
   - Attach `/tmp/containerguard-diagnostics.txt`

3. **Discussions:**
   - https://github.com/muralipala1504/containerguard-pro/discussions

---

## 📚 Related Documentation

- **README.md** - Project overview
- **INSTALL.md** - Installation guide
- **ARCHITECTURE.md** - Technical architecture
- **API.md** - API reference

---

**Built with ❤️ for the Docker community**
