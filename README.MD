# 🎓 Smart Face Attendance System  

> **AI-powered attendance management system with enterprise features, dual IN/OUT tracking, multi-photo registration, and advanced analytics.**  

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![DeepFace](https://img.shields.io/badge/DeepFace-0.0.79-green.svg)](https://github.com/serengil/deepface)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

---

## 🌟 Overview  

The **Smart Face Attendance System** revolutionizes attendance with **real-time AI face recognition**.  
Built for **universities & enterprises**, it ensures **accuracy (99.5%)**, **robust security**, and **intuitive analytics** — all in a sleek, production-ready system.  

✨ Think of it as your **next-gen biometric attendance manager**.  

---

## 🎯 Features  

### 🔹 Core Functionality  
- 🎭 **Face Recognition** – ArcFace + RetinaFace for near-perfect accuracy  
- 📸 **Multi-Photo Registration** – 2-5 photos per person for reliability  
- 🔄 **Dual IN/OUT Tracking** – Smarter attendance logs  
- ⏰ **Real-Time Processing** – Millisecond precision attendance marking  
- 📊 **Course Management** – 5 departments supported out-of-the-box  

### 🔹 Authentication & Security  
- 🔐 **Secure Login** – SHA-256 encryption + salt  
- 👥 **Role-Based Access** – Admin & Student roles  
- 🛡️ **Session Security** – Auto-logout, activity logging  
- 🔑 **Password Recovery** – Token-based reset system  

### 🔹 Analytics & Reporting  
- 📈 **Trends** – Daily, weekly, monthly analysis  
- 🏆 **Course-wise Comparisons**  
- 📊 **Interactive Charts** – Plotly-powered  
- 📤 **Export Reports** – CSV, Excel  
- ⏰ **Peak Hour Insights** – Identify busiest times  

---

## 📸 Screenshots  

### A glimpse of the system in action  

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 185256.png" width="45%"/>
  <img src="./assets/Screenshot 2025-09-25 185422.png" width="45%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 185634.png" width="45%"/>
  <img src="./assets/Screenshot 2025-09-25 185732.png" width="45%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 185904.png" width="45%"/>
  <img src="./assets/Screenshot 2025-09-25 185950.png" width="45%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190035.png" width="45%"/>
  <img src="./assets/Screenshot 2025-09-25 190106.png" width="45%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190140.png" width="45%"/>
  <img src="./assets/Screenshot 2025-09-25 190203.png" width="45%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190233.png" width="45%"/>
  <img src="./assets/Screenshot 2025-09-25 190306.png" width="45%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190337.png" width="45%"/>
  <img src="./assets/Screenshot 2025-09-25 190550.png" width="45%"/>
</p>

<p align="center">
  <img src="./assets/Screenshot 2025-09-25 190710.png" width="45%"/>
</p>

---

## 🏗️ Tech Stack  

| Layer             | Technology        | Purpose                                  |
| ----------------- | ----------------- | ---------------------------------------- |
| **Frontend**      | Streamlit         | Interactive web interface with modern UI |
| **Backend**       | Python 3.8+       | Core application logic and APIs          |
| **Database**      | SQLite            | Lightweight, ACID-compliant database     |
| **AI/ML**         | DeepFace, ArcFace | Face recognition and encoding            |
| **Detection**     | RetinaFace        | Robust face detection in images          |
| **Visualization** | Plotly            | Interactive analytics & charts           |

---

## 🚀 Quick Start  

```bash
# Clone repository
git clone https://github.com/yourusername/smart-face-attendance.git
cd smart-face-attendance

# Install dependencies
pip install -r requirements.txt

# Run the system
streamlit run main.py
