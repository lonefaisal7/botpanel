#!/usr/bin/env bash
# =============================================================================
#  update.sh  —  Update Bot Hosting Panel from the repository
#  Usage     : sudo bash /opt/botpanel/update.sh
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

if [ ! -d "$INSTALL_DIR" ]; then
  err "BotPanel not found at $INSTALL_DIR. Is it installed?"
fi

info "=== Bot Hosting Panel Updater ==="

# ── 1. Pull latest code ──────────────────────────────────────────────────────
cd "$INSTALL_DIR"

if [ -d ".git" ]; then
  info "Pulling latest changes from repository…"
  git fetch --all
  git reset --hard origin/main
  ok "Code updated from git."
else
  info "No git repo found — re-cloning…"
  TMPDIR=$(mktemp -d)
  git clone https://github.com/lonefaisal7/botpanel "$TMPDIR"
  # Preserve user data: bots/, uploads/, bots.db, credentials.json, venv/
  for item in app frontend requirements.txt setup.sh update.sh uninstall.sh run.sh set_password.py README.md; do
    if [ -e "$TMPDIR/$item" ]; then
      rm -rf "$INSTALL_DIR/$item"
      cp -r "$TMPDIR/$item" "$INSTALL_DIR/$item"
    fi
  done
  rm -rf "$TMPDIR"
  ok "Code updated from fresh clone."
fi

# ── 2. Update Python dependencies ────────────────────────────────────────────
info "Updating Python dependencies…"
PYTHON3=$(command -v python3)
if [ ! -d "$INSTALL_DIR/venv" ]; then
  "$PYTHON3" -m venv "$INSTALL_DIR/venv"
fi
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip -q
pip install -r requirements.txt -q
ok "Dependencies updated."

# ── 3. Fix permissions ────────────────────────────────────────────────────────
chmod +x "$INSTALL_DIR/run.sh" "$INSTALL_DIR/setup.sh"
[ -f "$INSTALL_DIR/update.sh" ] && chmod +x "$INSTALL_DIR/update.sh"
[ -f "$INSTALL_DIR/uninstall.sh" ] && chmod +x "$INSTALL_DIR/uninstall.sh"
mkdir -p "$INSTALL_DIR/bots" "$INSTALL_DIR/uploads"

# ── 4. Restart service ───────────────────────────────────────────────────────
info "Restarting botpanel service…"
systemctl daemon-reload
systemctl restart botpanel
ok "Service restarted."

echo ""
echo -e "${GREEN}Update complete! BotPanel is running the latest version.${NC}"
echo -e "  Dashboard : http://$(hostname -I | awk '{print $1}'):8000"
echo -e "  Logs      : journalctl -u botpanel -f"
echo ""
