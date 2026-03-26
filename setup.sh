#!/usr/bin/env bash
# =============================================================================
#  setup.sh  —  One-command installer for Bot Hosting Panel
#  Repo   : https://github.com/lonefaisal7/botpanel
#  Usage  : curl -sSL https://raw.githubusercontent.com/lonefaisal7/botpanel/main/setup.sh | sudo bash
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

INSTALL_DIR="/opt/botpanel"

info "=== Bot Hosting Panel Installer ==="
info "Repo        : https://github.com/lonefaisal7/botpanel"
info "Install dir : $INSTALL_DIR"

# ── 1. System update ──────────────────────────────────────────────────────────
info "Updating system packages…"
apt-get update -y && apt-get upgrade -y
ok "System updated."

# ── 2. Base dependencies ──────────────────────────────────────────────────────
info "Installing system dependencies…"
apt-get install -y \
  python3 python3-venv python3-pip \
  curl wget git unzip ca-certificates \
  gnupg lsb-release software-properties-common
ok "System dependencies installed."

# ── Detect usable Python 3 ──────────────────────────────────────────────────
PYTHON3=$(command -v python3)
if [ -z "$PYTHON3" ]; then
  err "python3 not found after install. Cannot continue."
fi
PY_VER=$("$PYTHON3" --version | awk '{print $2}')
info "Detected Python: $PYTHON3 ($PY_VER)"

# ── 3. Docker ────────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  info "Installing Docker…"
  curl -fsSL https://get.docker.com | bash
  systemctl enable --now docker
  ok "Docker installed."
else
  ok "Docker already installed: $(docker --version)"
fi

# Add invoking user to docker group
if [ -n "$SUDO_USER" ]; then
  usermod -aG docker "$SUDO_USER"
  info "Added $SUDO_USER to docker group (re-login required for group to take effect)."
fi

# ── 4. Clone / update repo ───────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
  info "Updating existing installation…"
  git -C "$INSTALL_DIR" pull
else
  info "Cloning https://github.com/lonefaisal7/botpanel …"
  if [ -f "app/main.py" ]; then
    info "Local source detected — copying to $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    cp -r . "$INSTALL_DIR/"
  else
    git clone https://github.com/lonefaisal7/botpanel "$INSTALL_DIR"
  fi
fi
ok "Source code ready at $INSTALL_DIR."

cd "$INSTALL_DIR"

# ── 5. Python virtual environment ────────────────────────────────────────────
info "Creating Python virtual environment…"
"$PYTHON3" -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ok "Python dependencies installed."

# ── 6. Directories & permissions ─────────────────────────────────────────────
info "Creating required directories…"
mkdir -p bots uploads
chmod 755 bots uploads
chmod +x run.sh setup.sh update.sh uninstall.sh
ok "Directories ready."

# ── 7. Admin credentials ─────────────────────────────────────────────────────
if [ -f "$INSTALL_DIR/.env" ]; then
  ok ".env already exists — keeping existing credentials."
else
  info "No .env file — admin account will be created on first web visit."
fi

# ── 8. Systemd service ───────────────────────────────────────────────────────
info "Creating systemd service: botpanel…"
cp "$INSTALL_DIR/botpanel.service" /etc/systemd/system/botpanel.service

systemctl daemon-reload
systemctl enable botpanel
systemctl restart botpanel
ok "Systemd service 'botpanel' started."

# ── 9. Firewall ───────────────────────────────────────────────────────────────
if command -v ufw &>/dev/null; then
  ufw allow 8000/tcp 2>/dev/null || true
  info "UFW: port 8000 opened."
fi

# ── Done ─────────────────────────────────────────────────────────────────────
# Prefer public IP for VPS deploy, fallback to local host interface if unavailable
SERVER_IP=$(hostname -I | awk '{print $1}')
PUBLIC_IP=$(curl -sS --max-time 5 https://ifconfig.me || true)
if [ -n "$PUBLIC_IP" ]; then
  # ifconfig.me might return empty or an error, so keep fallback
  IP_ADDRESS=$PUBLIC_IP
else
  IP_ADDRESS=$SERVER_IP
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅  Bot Hosting Panel is LIVE!                         ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  🌐  Dashboard  →  http://${IP_ADDRESS}:8000               ${NC}"
echo -e "${GREEN}║  📖  API Docs   →  http://${IP_ADDRESS}:8000/docs          ${NC}"
echo -e "${GREEN}║  📋  Logs       →  journalctl -u botpanel -f              ║${NC}"
echo -e "${GREEN}║  ⏹   Stop       →  systemctl stop botpanel               ║${NC}"
echo -e "${GREEN}║  🔄  Restart    →  systemctl restart botpanel            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
