# Smart Face Attendance System  

**An AI-powered attendance management system with enterprise features, dual IN/OUT tracking, multi-photo registration, and advanced analytics.**  

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![DeepFace](https://img.shields.io/badge/DeepFace-0.0.90+-green.svg)](https://github.com/serengil/deepface)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

---

## Overview  

The **Smart Face Attendance System** revolutionizes attendance tracking through **real-time AI-based face recognition**.  
Designed for universities, enterprises, and organizations, it ensures:  

- High accuracy (up to **99.5%**)  
- Strong security features  
- Real-time data insights and analytics  

This project provides a modern alternative to traditional biometric and manual attendance systems.  

---

## Real-World Problem & Solution  

### The Problem  
- Manual attendance wastes **10–15 minutes per class/meeting**.  
- Conventional biometric systems (fingerprint, RFID) face issues like **proxy attendance, hygiene concerns, and delays**.  
- A study by *Deloitte (2022)* revealed that organizations lose **$37 billion annually** due to inaccurate time and attendance tracking.  

### The Solution  
The **Smart Face Attendance System** solves these issues by offering:  
- **Touchless, real-time face recognition** → reduces delays.  
- **Dual IN/OUT tracking** → prevents proxy attendance.  
- **Multi-photo registration** → ensures recognition accuracy even under different lighting/angles.  
- **Automated analytics and reporting** → saves administrative overhead by up to **40%**.  

---

## Features  

### Core Functionality  
- Face Recognition with **ArcFace + RetinaFace** (configurable thresholds and margin for safer matching)  
- Multi-Photo Registration (2–5 photos per person)  
- Dual IN/OUT Tracking for precise logs  
- Real-Time Processing with millisecond accuracy  
- Built-in Course & Department Management  
- Optional **live mask / covering check** (YOLO-World + WebRTC path) when enabled  

### Authentication & Security  
- **bcrypt** password hashing with migration from legacy salted SHA-256 where applicable  
- Role-Based Access (Admin & Student)  
- Session handling with configurable timeouts  
- Password reset flow with token expiry and rate limiting  
- Optional **admin TOTP (2FA)** via `ENABLE_ADMIN_2FA`  
- Audit-friendly security settings (see `.env` / `config/settings.py`)  

### Analytics & Reporting  
- Daily, Weekly, and Monthly Trends  
- Course-Wise Comparisons  
- Interactive Charts with Plotly  
- Export options including **CSV, Excel, and PDF**  
- Peak Hour Usage Insights  
- **System Health** view for operational checks  

---

## Screenshots  

### System in Action  

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 185256.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 185422.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 185634.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 185732.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 185904.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 185950.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190035.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190106.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190140.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190203.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190233.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190306.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190337.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190550.png" width="80%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190710.png" width="80%"/>
</p>

---

## Tech Stack  

| Layer             | Technology              | Purpose                                      |
| ----------------- | ----------------------- | -------------------------------------------- |
| Frontend          | Streamlit               | Interactive web UI                           |
| Backend           | Python 3.9+             | Application logic                            |
| Database          | SQLite                  | Lightweight, file-based storage (`data/`)    |
| AI / ML           | DeepFace, ArcFace       | Face embeddings and verification             |
| Detection         | RetinaFace              | Face detection in images                     |
| Optional vision   | Ultralytics YOLO-World  | Open-vocabulary mask / no-mask cues          |
| Visualization     | Plotly                  | Analytics charts                             |
| Reporting         | fpdf2                   | PDF exports                                  |
| Security          | bcrypt, cryptography    | Password hashing and crypto utilities        |

---

## Quick Start  

### 1. Clone and install  

```bash
git clone https://github.com/MohammadUsman00/smart-face-attendance-system_usmandar820-gmail.com.git
cd smart-face-attendance-system_usmandar820-gmail.com

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment  

Create a `.env` file in the project root from `.env.example` (not committed). The app fails fast if required security settings are missing or still use demo values. Set at least:

- `ADMIN_EMAIL`, `ADMIN_PASSWORD` — first admin bootstrap (see migration / `ensure_admin_exists`)  
- `SECRET_KEY`, `SALT` — strong unique values; generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`  
- `BIOMETRIC_CACHE_ENABLED=false` by default. If you enable it, also set `BIOMETRIC_CACHE_ENCRYPTION_KEY` with a Fernet key.  
- Face recognition keys such as `RECOGNITION_THRESHOLD`, `RECOGNITION_MARGIN`, `MODEL_NAME`, `DETECTOR_BACKEND` as needed  

Configuration is read from **environment variables** (including values loaded by `python-dotenv` from `.env`).

### 3. Run locally  

```bash
streamlit run main.py
```

Open the URL shown in the terminal (default **http://localhost:8501**).

### 4. Run with Docker  

From the project root (same folder as `Dockerfile`):

```bash
docker compose up --build
```

To pass your local `.env` into the Compose service, add `env_file: [.env]` under `smart-attendance` in `docker-compose.yml` after creating `.env`.

Or with plain Docker:

```bash
docker build -t smart-face-attendance .
docker run -p 8501:8501 -v "%cd%/data:/app/data" -v "%cd%/logs:/app/logs" --env-file .env smart-face-attendance
```

On **Linux/macOS**, replace the volume paths with `$(pwd)/data` and `$(pwd)/logs`.

`docker-compose.yml` maps **8501**, persists `./data` and `./logs`, and sets `STREAMLIT_SERVER_PORT=8501`. The image starts Streamlit on **0.0.0.0:8501** so the port is reachable from the host.

### 5. Tests  

```bash
python -m pytest tests/ -q
```
