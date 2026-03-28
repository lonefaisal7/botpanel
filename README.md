# 🚀 Bot Hosting Panel

<p align="center">
  <img src="https://img.shields.io/github/stars/lonefaisal7/botpanel?style=for-the-badge" />
  <img src="https://img.shields.io/github/forks/lonefaisal7/botpanel?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Docker-Required-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
</p>

> ⚡ Self-hosted Telegram bot management panel powered by **FastAPI + Docker**

A modern, production-ready system to **deploy, manage, and monitor multiple Telegram bots** on your own VPS — with complete control over infrastructure, security, and scaling.

---

## 🎬 Demo Preview

<p align="center">
  <img src="https://github.com/user-attachments/assets/403e4fa7-3751-4556-b494-d129178e694f" width="100%" />
</p>

> 💡 Tip: Replace this image with a short GIF recording for higher engagement

---

## 🧠 Why Choose Bot Hosting Panel?

| Feature | This Panel | Typical Panels |
|--------|-----------|---------------|
| Full Ownership | ✅ | ❌ |
| Docker Isolation | ✅ | ⚠️ Limited |
| No Subscription | ✅ | ❌ |
| Easy Deployment | ✅ | ⚠️ Complex |
| Open Source | ✅ | ❌ |
| Lightweight | ✅ | ❌ |

👉 Built for developers who want **control, simplicity, and performance** — without SaaS limitations.

---

## ✨ Highlights

- 🧠 Fully self-hosted — no third-party dependency
- 🐳 Docker-based isolation per bot
- ⚡ FastAPI backend (high performance)
- 🎛️ Clean and responsive UI
- 🔐 Secure authentication system
- 📦 One-command install & update

---

## 🧩 Architecture

```
User → Web UI → FastAPI → Docker Containers → Telegram Bots
```

- Each bot runs in its **own isolated container**
- Panel controls lifecycle + logs + deployment
- SQLite used (no external DB needed)

---

## 🔥 Features

### 🖥️ Dashboard
- Secure JWT authentication
- Upload `.py` / `.zip`
- Live bot logs viewer
- Auto-refresh UI

### 🐳 Runtime
- One container per bot
- Auto dependency install
- Resource limits (CPU / RAM)

### 🔐 Security
- Bcrypt password hashing
- Token-based API protection
- File validation + sanitization

### ⚙️ DevOps
- One-command install
- Update script
- Clean uninstall
- systemd service support

---

## ⚡ Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/lonefaisal7/botpanel/main/setup.sh | sudo bash
```

Then open:

```
http://YOUR_VPS_IP:8000
```

---

## 🛠️ Manual Setup

```bash
git clone https://github.com/lonefaisal7/botpanel
cd botpanel

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

chmod +x run.sh
./run.sh
```

---

## 📦 Usage Flow

1. Create admin account
2. Upload bot file
3. Deploy container
4. Monitor logs
5. Control lifecycle

---

## 🧰 Commands

```bash
systemctl status botpanel
journalctl -u botpanel -f
systemctl restart botpanel
```

---

## 🔄 Update

```bash
sudo bash /opt/botpanel/update.sh
```

---

## 🗑️ Uninstall

```bash
sudo bash /opt/botpanel/uninstall.sh --yes
```

---

## 👨‍💻 Authors

**LONE FAISAL**  
https://t.me/lonefaisal

**PROFESSOR**  
https://t.me/trueprofessor

---

## 📢 Community

- https://t.me/arrow_network  
- https://t.me/kmri_network_reborn

---

## ⭐ Support

If this project helps you:

⭐ Star the repo  
🔁 Share it  
🛠️ Contribute improvements

---

## 📄 License

MIT License

