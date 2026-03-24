# 🤖 Bot Hosting Panel

A **self-hosted Telegram bot hosting panel** built with FastAPI + Docker.
Deploy, manage, and monitor your Telegram bots from a clean web dashboard — running on your own Ubuntu VPS.

> **Repository:** [https://github.com/lonefaisal7/botpanel](https://github.com/lonefaisal7/botpanel)

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔒 JWT Auth | Login required — bcrypt-hashed password, JWT Bearer tokens |
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
| 🛡 Resource limits | 200MB RAM + 0.5 CPU per bot container |

---

## 🚀 One-Command Install

```bash
curl -sSL https://raw.githubusercontent.com/lonefaisal7/botpanel/main/setup.sh | sudo bash
```

After install, open **http://YOUR\_VPS\_IP:8000** in your browser. On first visit you will see a **Create Admin Account** screen where you set your username and password. Credentials are securely stored using bcrypt hashing. On subsequent visits you will see the normal login screen.

> **Prerequisites:** Fresh Ubuntu 20.04/22.04/24.04 VPS with port **8000** open.

---




## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/auth/setup-status` | Check if admin account exists |
| `POST` | `/api/auth/setup` | Create admin account (first run only) |
| `POST` | `/login` | Authenticate and receive JWT token |
| `POST` | `/api/bots/upload` | Upload bot (`file` + `bot_name`) |
| `GET`  | `/api/bots/list` | List all bots with live status |
| `POST` | `/api/bots/{id}/start` | Start bot container |
| `POST` | `/api/bots/{id}/stop` | Stop bot container |
| `POST` | `/api/bots/{id}/restart` | Restart bot container |
| `DELETE` | `/api/bots/{id}` | Delete bot (container + image + files) |
| `GET`  | `/api/bots/{id}/logs` | Get last 150 lines of Docker logs |
| `GET`  | `/health` | Health check |

All endpoints except `/login` and `/health` require `Authorization: Bearer <token>` header.

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

All containers run with `--restart unless-stopped`, 200MB memory limit, and 0.5 CPU limit.

---

## 🔒 Security

- **No default credentials** — first visit requires creating an admin account
- **JWT authentication** — Dashboard and API require Bearer token
- Passwords stored as **bcrypt hashes** in `.env` (never plain text)
- JWT tokens signed with a random SECRET\_KEY
- Only `.py` and `.zip` files accepted; 50 MB max upload
- Zip-slip / path traversal protection
- Bot code runs **exclusively inside Docker containers** with resource limits
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

## ❤️ Made with love by

- **LONE FAISAL** → [https://t.me/lonefaisal](https://t.me/lonefaisal)
- **Professor** → [https://t.me/trueprofessor](https://t.me/trueprofessor)

### 📢 Official Channels

- ✦ **Arrow Network** → [https://t.me/arrow_network](https://t.me/arrow_network)
- ✦ **KMRI Network** → [https://t.me/kmri_network_reborn](https://t.me/kmri_network_reborn)

---

## 📄 License

MIT — free to use, modify, and self-host.
