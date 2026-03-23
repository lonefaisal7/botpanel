#!/usr/bin/env bash
# =============================================================================
#  uninstall.sh  —  Safely remove Bot Hosting Panel
#  Usage        : sudo bash /opt/botpanel/uninstall.sh
# =============================================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

if [ "$EUID" -ne 0 ]; then
  err "Please run as root or with sudo."
fi

INSTALL_DIR="/opt/botpanel"

echo ""
echo -e "${YELLOW}=== Bot Hosting Panel Uninstaller ===${NC}"
echo ""
echo "This will:"
echo "  1. Stop and remove the botpanel systemd service"
echo "  2. Remove all files from $INSTALL_DIR"
echo "  3. Optionally stop and remove bot Docker containers/images"
echo ""
echo -e "${RED}WARNING: This action cannot be undone. Bot data will be deleted.${NC}"
echo ""

# Check for --yes flag for non-interactive confirmation
SKIP_CONFIRM=false
for arg in "$@"; do
  case "$arg" in
    --yes|-y) SKIP_CONFIRM=true ;;
  esac
done

if [ "$SKIP_CONFIRM" = false ]; then
  if [ -t 0 ]; then
    read -p "Are you sure you want to uninstall? (y/N): " REPLY
    if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
      echo "Cancelled."
      exit 0
    fi
  else
    err "Non-interactive mode: pass --yes to confirm uninstall."
  fi
fi

# ── 1. Stop & disable systemd service ────────────────────────────────────────
if systemctl is-active --quiet botpanel 2>/dev/null; then
  info "Stopping botpanel service…"
  systemctl stop botpanel
  ok "Service stopped."
fi

if systemctl is-enabled --quiet botpanel 2>/dev/null; then
  info "Disabling botpanel service…"
  systemctl disable botpanel
fi

if [ -f /etc/systemd/system/botpanel.service ]; then
  info "Removing systemd unit file…"
  rm -f /etc/systemd/system/botpanel.service
  systemctl daemon-reload
  ok "Systemd service removed."
fi

# ── 2. Stop bot Docker containers & remove images ────────────────────────────
if command -v docker &>/dev/null; then
  info "Cleaning up bot Docker containers…"

  # Stop and remove containers with the bot- prefix
  BOT_CONTAINERS=$(docker ps -a --filter "name=bot-" --format "{{.ID}}" 2>/dev/null || true)
  if [ -n "$BOT_CONTAINERS" ]; then
    echo "$BOT_CONTAINERS" | xargs -r docker rm -f 2>/dev/null || true
    ok "Bot containers removed."
  else
    info "No bot containers found."
  fi

  # Remove botpanel images
  BOT_IMAGES=$(docker images --filter "reference=botpanel-*" --format "{{.ID}}" 2>/dev/null || true)
  if [ -n "$BOT_IMAGES" ]; then
    echo "$BOT_IMAGES" | xargs -r docker rmi -f 2>/dev/null || true
    ok "Bot Docker images removed."
  else
    info "No bot images found."
  fi
fi

# ── 3. Remove install directory ───────────────────────────────────────────────
if [ -d "$INSTALL_DIR" ]; then
  info "Removing $INSTALL_DIR…"
  rm -rf "$INSTALL_DIR"
  ok "Install directory removed."
fi

# ── 4. Close firewall port (optional, non-fatal) ─────────────────────────────
if command -v ufw &>/dev/null; then
  ufw delete allow 8000/tcp 2>/dev/null || true
  info "UFW: port 8000 rule removed."
fi

echo ""
echo -e "${GREEN}Bot Hosting Panel has been uninstalled.${NC}"
echo ""
echo "Docker and Python were NOT removed (they may be used by other software)."
echo "To remove them manually if desired:"
echo "  sudo apt remove docker-ce docker-ce-cli containerd.io"
echo "  sudo apt remove python3 python3-venv python3-pip"
echo ""
