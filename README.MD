# Smart Face Attendance System

Touchless attendance with face recognition, dual IN/OUT tracking, role-based admin controls, analytics, and biometric-data safety features.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![DeepFace](https://img.shields.io/badge/DeepFace-0.0.90+-green.svg)](https://github.com/serengil/deepface)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What Is Implemented

- Attendance-first workflow in the dashboard/sidebar
- Face recognition with configurable threshold and ambiguity margin
- Multi-photo student enrollment (2-5 photos)
- Auto IN/OUT attendance marking
- Optional mask/covering gate before attendance marking
- Analytics, CSV/Excel/PDF exports, and system health view
- Admin controls with stronger safeguards for destructive actions
- Security hardening: required env secrets, bcrypt auth, optional admin TOTP
- Biometric lifecycle controls:
  - encrypted embedding cache only when explicitly enabled
  - hard-delete-on-student-delete toggle
  - retention-based biometric purge action for inactive students
- CI with focused tests + secret scanning

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
git clone https://github.com/MohammadUsman00/smart-face-attendance-system.git
cd smart-face-attendance-system

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment  

Create `.env` from `.env.example` (not committed).  
The app fails fast if required security settings are missing or unsafe.

Required minimum:

- `ADMIN_EMAIL`, `ADMIN_PASSWORD` — first admin bootstrap (see migration / `ensure_admin_exists`)  
- `SECRET_KEY`, `SALT` — strong unique values; generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`  
- `BIOMETRIC_CACHE_ENABLED=false` by default. If enabled, also set `BIOMETRIC_CACHE_ENCRYPTION_KEY` (Fernet key).  
- `BIOMETRIC_RETENTION_DAYS`, `BIOMETRIC_HARD_DELETE_ON_STUDENT_DELETE` — biometric retention/deletion behavior.  
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
python -m pytest tests/test_password_hashing.py tests/test_recognition_decision.py tests/test_reset_expires_parse.py tests/test_security_config.py tests/test_student_repository.py tests/test_attendance_pipeline.py tests/test_mask_gate.py -q
```

---

## Admin Panel

Admin features currently include:
- Student management (enroll/list/delete/export)
- Live attendance marking and attendance record browsing
- Analytics + health page
- User management
- Danger Zone with typed confirmation + admin password re-auth
- Biometric retention purge action

Admin credentials are controlled by `.env`:
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
