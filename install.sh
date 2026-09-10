#!/bin/bash
# ContainerGuard Pro - One-Line Installer
# Usage: curl -sSL https://raw.githubusercontent.com/muralipala1504/containerguard-pro/main/install.sh | bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

echo "═══════════════════════════════════════════════════════════════"
echo "  🔐 ContainerGuard Pro - Autonomous Docker Agent"
echo "  Version: 1.0.0"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if [[ $EUID -eq 0 ]]; then
    print_warning "Running as root - this is not recommended"
    INSTALL_USER=$SUDO_USER
else
    INSTALL_USER=$USER
fi
print_info "Installing for user: $INSTALL_USER"

# Check OS
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    print_info "Detected OS: $ID $VERSION_ID"
else
    print_error "Cannot detect OS."
    exit 1
fi

# Check Docker
# Check and install Docker if missing
if ! command -v docker &> /dev/null; then
    print_warning "Docker is not installed. Installing..."

    # Detect OS and install Docker
    if [[ "$ID" == "almalinux" ]] || [[ "$ID" == "rhel" ]] || [[ "$ID" == "centos" ]]; then
        sudo dnf install -y dnf-utils
        sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
        sudo dnf install -y docker-ce docker-ce-cli containerd.io
    elif [[ "$ID" == "ubuntu" ]] || [[ "$ID" == "debian" ]]; then
        sudo apt update
        sudo apt install -y docker.io
    else
        print_error "Unsupported OS. Please install Docker manually."
        exit 1
    fi

    sudo systemctl enable --now docker
    sudo usermod -aG docker $INSTALL_USER
    print_success "Docker installed successfully"
else
    DOCKER_VERSION=$(docker --version | cut -d" " -f3 | tr -d ",")
    print_success "Docker found: $DOCKER_VERSION"
fi
print_success "Docker found: $(docker --version | cut -d' ' -f3 | tr -d ',')"
# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed."
    exit 1
fi
print_success "Python found: $(python3 --version | cut -d' ' -f2)"

INSTALL_DIR="/home/$INSTALL_USER/containerguard-pro"
print_info "Installation directory: $INSTALL_DIR"

if [[ -d "$INSTALL_DIR" ]]; then
    print_warning "Directory exists: $INSTALL_DIR"
    read -p "Remove existing installation? (y/N) " -n 1 -r </dev/tty
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing installation..."
        rm -rf "$INSTALL_DIR"
    else

        print_error "Installation cancelled."
        exit 1
    fi
fi

print_info "Cloning Pro repository..."
git clone https://github.com/muralipala1504/containerguard-pro.git "$INSTALL_DIR"
cd "$INSTALL_DIR"

print_info "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

print_info "Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

print_info "Installing OAuth dependencies for GitHub authentication..."
pip install flask flask-login authlib > /dev/null 2>&1

# Apply SELinux context
if command -v getenforce &> /dev/null && [[ $(getenforce) == "Enforcing" ]]; then
    print_info "Applying SELinux context..."
    sudo chcon -R -t bin_t "$INSTALL_DIR"/venv/bin/
    sudo chcon -t bin_t "$INSTALL_DIR/agent/run-pro.sh" 2>/dev/null || true
    sudo chcon -t bin_t "$INSTALL_DIR/dashboard/run.sh" 2>/dev/null || true

# Create log files with proper permissions
print_info "Creating log files..."
sudo touch /var/log/containerguard-pro.log
sudo touch /var/log/containerguard-pro-error.log
sudo touch /var/log/containerguard-dashboard.log
sudo touch /var/log/containerguard-dashboard-error.log
sudo chown $INSTALL_USER:$INSTALL_USER /var/log/containerguard-pro.log
sudo chown $INSTALL_USER:$INSTALL_USER /var/log/containerguard-pro-error.log
sudo chown $INSTALL_USER:$INSTALL_USER /var/log/containerguard-dashboard.log
sudo chown $INSTALL_USER:$INSTALL_USER /var/log/containerguard-dashboard-error.log
sudo chmod 644 /var/log/containerguard-pro.log
sudo chmod 644 /var/log/containerguard-pro-error.log
sudo chmod 644 /var/log/containerguard-dashboard.log
sudo chmod 644 /var/log/containerguard-dashboard-error.log
print_success "Log files created"
fi

# Create Multi-Host config
print_info "Configuring Multi-Host..."
sudo mkdir -p /etc/containerguard
sudo tee /etc/containerguard/hosts.conf << 'HOSTSEOF'
{
  "hosts": [
    {"name": "local", "host": "unix:///var/run/docker.sock"},
    {"name": "remote", "host": "tcp://192.168.217.170:2375"}
  ]
}
HOSTSEOF

# Create systemd service
print_info "Installing systemd service..."
print_info "Installing systemd services..."
sudo cp deploy/containerguard-pro.service /etc/systemd/system/containerguard-pro.service
sudo cp deploy/containerguard-dashboard.service /etc/systemd/system/containerguard-dashboard.service
sudo sed -i "s/\$INSTALL_USER/$INSTALL_USER/g" /etc/systemd/system/containerguard-pro.service
sudo sed -i "s/\$INSTALL_USER/$INSTALL_USER/g" /etc/systemd/system/containerguard-dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable containerguard-pro
sudo systemctl enable containerguard-dashboard
sudo systemctl start containerguard-pro
sudo systemctl start containerguard-dashboard

print_info "Configuring firewall for dashboard..."
if ! systemctl is-active --quiet firewalld 2>/dev/null; then
    print_info "Starting firewalld..."
    sudo systemctl start firewalld 2>/dev/null || true
    sudo systemctl enable firewalld 2>/dev/null || true
fi
if command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --add-port=7860/tcp --permanent 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true
    print_success "Firewall port 7860 opened"
else
    print_warning "firewalld not found. Please open port 7860 manually."

# Create .env file
cat > "$INSTALL_DIR/.env" << 'ENVEOF'
DOCKER_HOST=unix:///var/run/docker.sock
AGENT_INTERVAL=30
LOG_LEVEL=INFO
ENVEOF
print_success "Configuration file created: .env"
fi

print_success "✅ ContainerGuard Pro installation complete!"
echo ""
echo "📋 Installation Summary:"
echo "  📁 Location: $INSTALL_DIR"
echo "  🔧 Service: containerguard-pro (systemd)"
echo "  📊 Dashboard: http://$(hostname -I | awk '{print $1}'):7860"
echo "  📝 Logs: /var/log/containerguard-pro.log"
echo "  🔐 Status: sudo systemctl status containerguard-pro"
echo ""
echo "🔗 GitHub: https://github.com/muralipala1504/containerguard-pro"
