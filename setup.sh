#!/usr/bin/env bash
# =============================================================================
#  setup.sh  —  One-command installer for Bot Hosting Panel
#  Usage:  curl -sSL https://raw.githubusercontent.com/<user>/<repo>/main/setup.sh | bash
# =============================================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Root check ────────────────────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
  err "Please run as root or with sudo."
fi

INSTALL_DIR="/opt/bot-hosting-panel"
REPO_URL="https://github.com/YOUR_USERNAME/bot-hosting-panel"   # ← update before publishing

info "=== Bot Hosting Panel Installer ==="
info "Install directory: $INSTALL_DIR"

# ── 1. System update ──────────────────────────────────────────────────────────
info "Updating system packages…"
apt-get update -y && apt-get upgrade -y
ok "System updated."

# ── 2. Base dependencies ──────────────────────────────────────────────────────
info "Installing system dependencies…"
apt-get install -y \
  python3.11 python3.11-venv python3-pip \
  curl wget git unzip ca-certificates \
  gnupg lsb-release software-properties-common
ok "System dependencies installed."

# ── 3. Docker ────────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  info "Installing Docker…"
  curl -fsSL https://get.docker.com | bash
  systemctl enable --now docker
  ok "Docker installed."
else
  ok "Docker already installed: $(docker --version)"
fi

# Add current user to docker group (if not root)
if [ -n "$SUDO_USER" ]; then
  usermod -aG docker "$SUDO_USER"
  info "Added $SUDO_USER to docker group (re-login required for effect)."
fi

# ── 4. Clone / update repo ───────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
  info "Updating existing installation…"
  git -C "$INSTALL_DIR" pull
else
  info "Cloning repository…"
  # If running via curl pipe, clone; else copy from current dir
  if [ -f "app/main.py" ]; then
    info "Local source detected — copying to $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    cp -r . "$INSTALL_DIR/"
  else
    git clone "$REPO_URL" "$INSTALL_DIR"
  fi
fi
ok "Source code ready at $INSTALL_DIR."

cd "$INSTALL_DIR"

# ── 5. Python virtual environment ────────────────────────────────────────────
info "Creating Python virtual environment…"
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ok "Python dependencies installed."

# ── 6. Directories & permissions ─────────────────────────────────────────────
info "Creating required directories…"
mkdir -p bots uploads
chmod 755 bots uploads
chmod +x run.sh setup.sh
ok "Directories created."

# ── 7. Systemd service ───────────────────────────────────────────────────────
info "Creating systemd service…"
cat > /etc/systemd/system/botpanel.service << EOF
[Unit]
Description=Bot Hosting Panel
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=botpanel

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable botpanel
systemctl restart botpanel
ok "Systemd service started."

# ── 8. Firewall hint ─────────────────────────────────────────────────────────
if command -v ufw &>/dev/null; then
  ufw allow 8000/tcp 2>/dev/null || true
  info "UFW: port 8000 allowed."
fi

# ── Done ─────────────────────────────────────────────────────────────────────
SERVER_IP=$(hostname -I | awk '{print $1}')
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅  Bot Hosting Panel is LIVE!             ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  URL  →  http://${SERVER_IP}:8000            ${NC}"
echo -e "${GREEN}║  Logs →  journalctl -u botpanel -f           ${NC}"
echo -e "${GREEN}║  Stop →  systemctl stop botpanel             ${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
