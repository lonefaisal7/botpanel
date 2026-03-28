# Bot Hosting Panel

A self-hosted Telegram bot management panel built with **FastAPI + Docker**.
Deploy, run, monitor, and control multiple bots from a clean web dashboard on your own VPS.

Repository: [github.com/lonefaisal7/botpanel](https://github.com/lonefaisal7/botpanel)

## Project Overview

**Bot Hosting Panel** is designed for users who want full control over Telegram bot hosting without relying on third-party dashboards.
Each bot runs in an isolated Docker container, while the panel provides a simple web UI for deployment, lifecycle management, and logs.

### Why this project

- Self-hosted control over your bots and data
- Isolated runtime per bot using Docker
- Beginner-friendly web interface for daily operations
- Simple update and uninstall workflow

## Features

### Core Panel Features

- Secure login with JWT authentication
- Upload bot files as `.py` or `.zip`
- Start, stop, restart, and delete bots from dashboard
- Live bot logs in a modal viewer
- Auto-refreshing dashboard state

### Runtime & Isolation

- Dedicated Docker container per bot
- Auto-generated Dockerfile for deployments
- Automatic dependency installation from `requirements.txt`
- Resource limits per container (memory and CPU)

### Data & Security

- SQLite-based storage (no external DB required)
- Bcrypt-hashed credentials
- Path sanitization and upload validation
- Protected API routes with Bearer token auth

### Operations

- One-command install script
- One-command update script
- Clean uninstall script with interactive and non-interactive modes

## Quick Start (One-Command Install)

Use this on a fresh Ubuntu VPS:

```bash
curl -sSL https://raw.githubusercontent.com/lonefaisal7/botpanel/main/setup.sh | sudo bash
```

After installation:

1. Open `http://YOUR_VPS_IP:8000`
2. On first visit, create your admin account
3. Log in and start deploying bots

Recommended environment:

- Ubuntu 20.04 / 22.04 / 24.04
- Port `8000` open
- Docker available (installer handles this if missing)

## Manual Installation & Setup

```bash
git clone https://github.com/lonefaisal7/botpanel
cd botpanel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x run.sh
./run.sh
```

Then open:

- Dashboard: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

Optional: set admin password manually before first login:

```bash
python3 set_password.py
```

## Usage Guide

### 1. Log In / Initial Setup

- First run: create admin account from setup screen
- Next runs: log in using your configured credentials

### 2. Deploy a Bot

- Upload either:
  - A single `.py` bot file
  - A `.zip` archive containing bot source files
- Assign a bot name during upload

### 3. Manage Bots

Inside **Deployed Bots**, you can:

- Start
- Stop
- Restart
- Delete
- Open logs

### 4. View Logs

Use the logs action on any deployed bot to inspect runtime output directly in dashboard.

## Commands Reference

### Service Commands

```bash
systemctl status botpanel
journalctl -u botpanel -f
systemctl restart botpanel
systemctl stop botpanel
```

### Update Panel

Pull latest code and restart service:

```bash
sudo bash /opt/botpanel/update.sh
```

### Uninstall Panel

Interactive uninstall:

```bash
sudo bash /opt/botpanel/uninstall.sh
```

Non-interactive uninstall:

```bash
sudo bash /opt/botpanel/uninstall.sh --yes
```

### Change Admin Password

```bash
sudo /opt/botpanel/venv/bin/python /opt/botpanel/set_password.py
```

## Screenshots



<img width="1919" height="912" alt="dashboard" src="https://github.com/user-attachments/assets/403e4fa7-3751-4556-b494-d129178e694f" />





## Branding & Contact

Built and maintained by **LONE FAISAL & PROFESSOR**.

- LONE FAISAL: [t.me/lonefaisal](https://t.me/lonefaisal)
- PROFESSOR: [t.me/trueprofessor](https://t.me/trueprofessor)

Official channels:

- ARROW NETWORK: [t.me/arrow_network](https://t.me/arrow_network)
- KMRI NETWORK: [t.me/kmri_network_reborn](https://t.me/kmri_network_reborn)

## License

MIT License.
