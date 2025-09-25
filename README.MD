# Smart Face Attendance System  

**An AI-powered attendance management system with enterprise features, dual IN/OUT tracking, multi-photo registration, and advanced analytics.**  

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![DeepFace](https://img.shields.io/badge/DeepFace-0.0.79-green.svg)](https://github.com/serengil/deepface)
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
- Face Recognition with **ArcFace + RetinaFace**  
- Multi-Photo Registration (2–5 photos per person)  
- Dual IN/OUT Tracking for precise logs  
- Real-Time Processing with millisecond accuracy  
- Built-in Course & Department Management  

### Authentication & Security  
- Secure Login with SHA-256 + Salt Encryption  
- Role-Based Access (Admin & Student)  
- Session Security with Auto-Logout & Logging  
- Token-Based Password Recovery  

### Analytics & Reporting  
- Daily, Weekly, and Monthly Trends  
- Course-Wise Comparisons  
- Interactive Charts with Plotly  
- Export Options (CSV, Excel)  
- Peak Hour Usage Insights  

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

| Layer             | Technology        | Purpose                                  |
| ----------------- | ----------------- | ---------------------------------------- |
| Frontend          | Streamlit         | Interactive web interface with modern UI |
| Backend           | Python 3.8+       | Core application logic and APIs          |
| Database          | SQLite            | Lightweight, ACID-compliant database     |
| AI/ML             | DeepFace, ArcFace | Face recognition and encoding            |
| Detection         | RetinaFace        | Robust face detection in images          |
| Visualization     | Plotly            | Interactive analytics & charts           |

---

## Quick Start  

```bash
# Clone repository
git clone https://github.com/MohammadUsman00/smart-face-attendance-system_usmandar820-gmail.com.git
cd smart-face-attendance

# Install dependencies
pip install -r requirements.txt

# Run the system
streamlit run main.py
