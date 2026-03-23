# 🤖 Bot Hosting Panel

A **self-hosted Telegram bot hosting panel** built with FastAPI + Docker.
Deploy, manage, and monitor your Telegram bots from a clean web UI — running on your own Ubuntu VPS.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📦 Upload bots | `.py` single file or `.zip` archive |
| 🐳 Docker isolation | Every bot runs in its own `python:3.11-slim` container |
| ⚙️ Auto Dockerfile | Generated per-bot with dependency install |
| ▶️ Start / ⏸ Stop / 🔄 Restart | Full container lifecycle control |
| 🗑 Delete | Removes container, image, and files |
| 📄 Live Logs | Tail Docker logs in a modal popup |
| 🔁 Auto-refresh | Dashboard polls every 8 seconds |
| 💾 SQLite DB | Lightweight — no external DB needed |

---

## 🚀 One-Command Install

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/bot-hosting-panel/main/setup.sh | sudo bash
```

After install, open **http://YOUR_VPS_IP:8000** in your browser.

> **Prerequisites:** A fresh Ubuntu 20.04/22.04/24.04 VPS with port **8000** open.

---

## 🛠 Manual Install

```bash
git clone https://github.com/YOUR_USERNAME/bot-hosting-panel
cd bot-hosting-panel
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
chmod +x run.sh
./run.sh
```

---

## 📁 Project Structure

```
bot-hosting-panel/
├── app/
│   ├── main.py               ← FastAPI app entry point
│   ├── models/bot.py         ← SQLAlchemy models + SQLite engine
│   ├── routes/bots.py        ← API route definitions
│   └── services/
│       ├── bot_service.py    ← Upload, start, stop, delete logic
│       └── docker_service.py ← Docker SDK wrapper
├── frontend/
│   └── index.html            ← Full SPA dashboard (vanilla JS)
├── bots/                     ← Bot source files (per bot_id folder)
├── uploads/                  ← Temporary upload staging
├── requirements.txt
├── setup.sh                  ← One-command VPS installer
├── run.sh                    ← Start the server
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/bots/upload` | Upload bot (`multipart/form-data`: `file`, `bot_name`) |
| `GET`  | `/api/bots/list` | List all bots with live status |
| `POST` | `/api/bots/{id}/start` | Start bot container |
| `POST` | `/api/bots/{id}/stop` | Stop bot container |
| `POST` | `/api/bots/{id}/restart` | Restart bot container |
| `DELETE` | `/api/bots/{id}` | Delete bot (container + image + files) |
| `GET`  | `/api/bots/{id}/logs` | Get last 150 lines of Docker logs |
| `GET`  | `/health` | Health check |

Interactive docs: **http://YOUR_VPS_IP:8000/docs**

---

## 📤 How to Upload a Bot

### Single file
Upload `bot.py` directly.

### Zip archive
Structure your zip as:
```
mybot.zip
└── bot.py            ← or main.py
└── requirements.txt  ← optional
└── config.py         ← any helper files
```

---

## 🐳 Auto-generated Dockerfile (per bot)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "-u", "bot.py"]
```

Containers run with `--restart unless-stopped`.

---

## 🔒 Security

- Only `.py` and `.zip` files accepted
- 50 MB max upload size
- Zip-slip protection (path traversal check)
- All bot code runs **exclusively inside Docker containers**
- File paths sanitized before use

---

## 🧩 Manage as a Service

```bash
# Check status
systemctl status botpanel

# View logs
journalctl -u botpanel -f

# Restart panel
systemctl restart botpanel

# Stop panel
systemctl stop botpanel
```

---

## 📌 VPS Requirements

- Ubuntu 20.04 / 22.04 / 24.04
- Minimum 1 GB RAM, 10 GB disk
- Port **8000** open in firewall / security group
- Docker daemon running

---

## 📸 Screenshots

> Dashboard automatically refreshes every 8 seconds.

```
http://YOUR_VPS_IP:8000   ←  Web Dashboard
http://YOUR_VPS_IP:8000/docs  ←  API Docs (Swagger UI)
```

---

## 📄 License

MIT — free to use, modify, and self-host.
