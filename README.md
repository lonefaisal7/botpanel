# 🤖 Bot Hosting Panel

A **self-hosted Telegram bot hosting panel** built with FastAPI + Docker.  
Deploy, manage, and monitor your Telegram bots from a clean web dashboard — running on your own Ubuntu VPS.

> **Repository:** [https://github.com/lonefaisal7/botpanel](https://github.com/lonefaisal7/botpanel)

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔒 Password Auth | Login required — bcrypt-hashed credentials, signed session cookies |
| 📦 Upload bots | `.py` single file or `.zip` archive |
| 🐳 Docker isolation | Every bot runs in its own `python:3.11-slim` container |
| ⚙️ Auto Dockerfile | Generated per-bot with auto dependency install |
| ▶️ Start / ⏸ Stop / 🔄 Restart | Full container lifecycle control |
| 🗑 Delete | Removes container, image, and all files |
| 📄 Live Logs | Tail Docker logs in a modal popup |
| 🔁 Auto-refresh | Dashboard polls every 8 seconds |
| 💾 SQLite DB | No external database needed |
| 🔄 One-command Update | `sudo bash /opt/botpanel/update.sh` |
| 🗑 Clean Uninstall | `sudo bash /opt/botpanel/uninstall.sh` |

---

## 🚀 One-Command Install

```bash
curl -sSL https://raw.githubusercontent.com/lonefaisal7/botpanel/main/setup.sh | sudo bash
```

The installer will prompt you to set an **admin password** for the web dashboard.

For non-interactive installs (e.g. CI/scripts):
```bash
sudo BOTPANEL_PASSWORD=yourpassword bash setup.sh
# or
sudo bash setup.sh --password=yourpassword
```

After install, open **http://YOUR\_VPS\_IP:8000** and log in with username `admin`.

> **Prerequisites:** Fresh Ubuntu 20.04/22.04/24.04 VPS with port **8000** open.

---

## 🛠 Manual Install

```bash
git clone https://github.com/lonefaisal7/botpanel
cd botpanel
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
chmod +x run.sh
./run.sh
```

---

## 📁 Project Structure

```
botpanel/
├── app/
│   ├── main.py               ← FastAPI app entry point
│   ├── auth.py               ← Authentication (bcrypt + signed sessions)
│   ├── models/bot.py         ← SQLAlchemy models + SQLite engine
│   ├── routes/
│   │   ├── bots.py           ← Bot API route definitions
│   │   └── auth.py           ← Login / logout routes
│   └── services/
│       ├── bot_service.py    ← Upload, start, stop, delete logic
│       └── docker_service.py ← Docker SDK wrapper
├── frontend/
│   ├── index.html            ← Full SPA dashboard (vanilla JS)
│   └── login.html            ← Login page
├── bots/                     ← Bot source files (per bot_id folder)
├── uploads/                  ← Temporary upload staging
├── credentials.json          ← Hashed admin credentials (auto-generated)
├── requirements.txt
├── setup.sh                  ← One-command VPS installer
├── update.sh                 ← One-command updater
├── uninstall.sh              ← Clean uninstaller
├── set_password.py           ← Admin password utility
├── run.sh                    ← Start the server manually
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/bots/upload` | Upload bot (`file` + `bot_name`) |
| `GET`  | `/api/bots/list` | List all bots with live status |
| `POST` | `/api/bots/{id}/start` | Start bot container |
| `POST` | `/api/bots/{id}/stop` | Stop bot container |
| `POST` | `/api/bots/{id}/restart` | Restart bot container |
| `DELETE` | `/api/bots/{id}` | Delete bot (container + image + files) |
| `GET`  | `/api/bots/{id}/logs` | Get last 150 lines of Docker logs |
| `GET`  | `/health` | Health check |

Interactive Swagger docs: **http://YOUR\_VPS\_IP:8000/docs**

---

## 📤 How to Upload a Bot

### Single `.py` file
Upload `bot.py` directly — must contain your bot's main logic.

### `.zip` archive
```
mybot.zip
├── bot.py            ← entry point (or main.py)
├── requirements.txt  ← optional, auto-installed
└── config.py         ← any helper files
```

---

## 🐳 Auto-Generated Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "-u", "bot.py"]
```

All containers run with `--restart unless-stopped`.

---

## 🔒 Security

- **Password authentication** — Dashboard and API require login (username: `admin`)
- Passwords stored as **bcrypt hashes** (never plain text)
- Sessions use **signed cookies** (itsdangerous) with 7-day expiry
- Only `.py` and `.zip` files accepted; 50 MB max upload
- Zip-slip / path traversal protection
- Bot code runs **exclusively inside Docker containers**
- File paths sanitized via `os.path.realpath`

### Change Admin Password

```bash
sudo /opt/botpanel/venv/bin/python /opt/botpanel/set_password.py
```

---

## 🧩 Manage the Panel Service

```bash
systemctl status botpanel       # Check status
journalctl -u botpanel -f       # Live logs
systemctl restart botpanel      # Restart
systemctl stop botpanel         # Stop
```

---

## 🔄 Update

Pull the latest code and restart the service in one step:

```bash
sudo bash /opt/botpanel/update.sh
```

This preserves your bot data, database, and credentials. Only the application code and dependencies are refreshed.

---

## 🗑 Uninstall

Completely remove Bot Hosting Panel, its service, bot containers, and images:

```bash
sudo bash /opt/botpanel/uninstall.sh
```

For non-interactive use: `sudo bash /opt/botpanel/uninstall.sh --yes`

Docker and Python are **not** removed (they may be used by other software).

---

## 📌 VPS Requirements

- Ubuntu 20.04 / 22.04 / 24.04
- Minimum 1 GB RAM, 10 GB disk
- Port **8000** open in firewall / security group
- Docker daemon running

---

## 👤 Maintained By

**Lone Faisal (lonefaisal7)**  
🔗 GitHub: https://github.com/lonefaisal7

<img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/telegram.svg" width="16"/> Telegram:
- https://t.me/lonefaisal  
- https://t.me/trueprofessor  

---

## 📢 Official Channels

1. ✦ **Arrow Network**  
   <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/telegram.svg" width="16"/> https://t.me/arrow_network  

2. ✦ **KMRI Network**  
   <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/telegram.svg" width="16"/> https://t.me/kmri_network_reborn  

## 📄 License

MIT — free to use, modify, and self-host.
