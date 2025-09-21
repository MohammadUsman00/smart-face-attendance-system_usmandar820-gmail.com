# 🎓 Smart Face Attendance System

> **Advanced AI-powered attendance management system with dual IN/OUT tracking, multi-photo registration, and comprehensive analytics dashboard**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![DeepFace](https://img.shields.io/badge/DeepFace-0.0.79-green.svg)](https://github.com/serengil/deepface)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

## 🌟 **Project Overview**

The Smart Face Attendance System is a cutting-edge, production-ready application that revolutionizes attendance management using advanced face recognition technology. Built with modern AI models and designed for real-world deployment in educational institutions and corporate environments.

### 🎯 **Key Features**

#### **🔹 Core Functionality**
- **🎭 Advanced Face Recognition** - ArcFace + RetinaFace for 99.5% accuracy
- **📸 Multi-Photo Registration** - 2-5 photos per person for enhanced recognition
- **🔄 Dual Tracking System** - Separate IN/OUT attendance with smart detection
- **⏰ Real-Time Processing** - Instant attendance marking with millisecond precision
- **📊 Course Management** - Support for 5 departments (CSE, CE, EE, BE, ME)

#### **🔹 Authentication & Security**
- **🔐 Secure Login System** - SHA-256 encryption with salt
- **🔑 Password Reset** - Token-based password recovery
- **👥 Role-Based Access** - Admin and User roles with proper permissions
- **🛡️ Session Management** - Secure session handling and auto-logout

#### **🔹 Analytics & Reporting**
- **📈 Advanced Analytics** - Daily/weekly/monthly attendance trends
- **🏆 Course-wise Analysis** - Department performance comparison
- **📊 Interactive Charts** - Plotly-powered visualizations
- **📤 Data Export** - CSV/Excel export with custom date ranges
- **⏰ Peak Hours Analysis** - Identify busy periods and patterns

#### **🔹 Admin Controls**
- **👨‍💼 Student Management** - Complete CRUD operations
- **👥 User Management** - Admin user creation and management
- **⚠️ Danger Zone** - System reset and bulk operations
- **🔍 Audit Logs** - Complete activity tracking
- **📋 Backup & Restore** - Data protection features

## 🏗️ **System Architecture**

### **📁 Project Structure**
smart-face-attendance/
├── 📄 app.py # Main Streamlit application
├── 📄 db.py # Database operations (SQLite)
├── 📄 auth.py # Authentication & user management
├── 📄 face_utils.py # Face recognition utilities
├── 📄 style.css # Modern UI styling
├── 📄 requirements.txt # Python dependencies
├── 📄 .env # Environment configuration
├── 📄 .gitignore # Git ignore rules
├── 📄 README.md # This documentation
├── 📁 photos/ # Student photo storage (auto-created)
└── 📊 attendance.db # SQLite database (auto-created)

### **🔧 Technical Stack**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Streamlit | Interactive web interface |
| **Backend** | Python 3.8+ | Core application logic |
| **Database** | SQLite | Lightweight, file-based database |
| **AI/ML** | DeepFace, ArcFace | Face recognition and encoding |
| **Detection** | RetinaFace | Face detection in images |
| **Visualization** | Plotly | Interactive charts and graphs |
| **Styling** | CSS3 | Modern, responsive UI design |

### **🎯 Database Schema**
-- Users table with authentication
CREATE TABLE users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
email TEXT UNIQUE NOT NULL,
password TEXT NOT NULL,
role TEXT DEFAULT 'user',
reset_token TEXT,
reset_token_expires TIMESTAMP,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students table with course information
CREATE TABLE students (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
roll_number TEXT UNIQUE NOT NULL,
email TEXT UNIQUE NOT NULL,
phone TEXT,
course TEXT NOT NULL DEFAULT 'CSE',
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Face embeddings for multi-photo support
CREATE TABLE face_embeddings (
id INTEGER PRIMARY KEY AUTOINCREMENT,
student_id INTEGER NOT NULL,
embedding TEXT NOT NULL,
photo_number INTEGER DEFAULT 1,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Dual attendance tracking (IN/OUT)
CREATE TABLE attendance (
id INTEGER PRIMARY KEY AUTOINCREMENT,
student_id INTEGER NOT NULL,
date DATE NOT NULL,
time_in TEXT,
time_out TEXT,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
UNIQUE(student_id, date)
);

## 🚀 **Quick Start Guide**

### **📋 Prerequisites**

- **Python 3.8+** ([Download](https://python.org/downloads/))
- **Webcam/Camera** (for attendance marking)
- **4GB RAM** (minimum) - 8GB recommended
- **2GB Storage** (for photos and database)

### **⚡ Installation**

#### **1. Clone/Download Project**
