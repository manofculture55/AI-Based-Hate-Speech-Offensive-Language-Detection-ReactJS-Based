# AI-Based Hate Speech & Offensive Language Detection  
**KRIXION Internship Project (Final Submission)**  

**Execution Mode:** Fully Offline (No Internet, No External APIs)  
**Supported Languages:** English, Hindi, Hinglish (Code-Mixed)  
**Frontend:** React (v18.12.0)
**Backend:** Flask (Python)  
**Database:** SQLite  
**ML Stack:** Scikit-learn, TensorFlow / PyTorch  
**Platform:** Windows / macOS / Linux  

---

## 1. Project Overview

This project is a fully offline, AI-powered web application designed to detect **Hate Speech**, **Offensive Language**, and **Normal Content** in multilingual social media text.

The system is specifically optimized for **Indian social media content**, where **Hindi–English code-mixed (Hinglish)** text is very common and often difficult to moderate using traditional tools.

The application analyzes user input text and classifies it into one of three categories:

- **Normal**
- **Offensive**
- **Hate Speech**

In addition to classification, the system provides **confidence scores**, **latency metrics**, **language detection**, **analytics dashboards**, **human feedback learning**, and an **industry-style API interface** — all while running completely offline on CPU.

---

## 2. Key Features

### 🔤 Multilingual Intelligence
- Supports **English**, **Hindi**, and **Hinglish**
- Automatically detects language type
- Handles code-mixed and transliterated text

### 🧠 AI & ML Models
- Classical ML: TF-IDF + Logistic Regression, SVM
- Deep Learning: BiLSTM (CPU optimized)
- Multiple models compared and analyzed
- Best-performing model used for inference

### 🔒 Fully Offline & Secure
- No internet connection required
- No cloud APIs used
- All models, data, and logs stored locally
- Privacy-first design

### ⚡ Fast & Efficient
- Average latency < **2 seconds**
- CPU-only execution
- Optimized inference pipeline

### 📊 Analytics & Insights
- Prediction history with pagination
- Class distribution charts
- Language distribution analysis
- Model accuracy comparison
- Confusion matrix & error analysis

### 🧑‍💻 Human-in-the-Loop Learning
- Feedback system for correcting wrong predictions
- Survey system for collecting human labels
- Flag-word intelligence for identifying harmful terms
- Accuracy improves over time using real user input

### 🛠️ Hidden Admin Panel
- Secure, password-protected admin access
- Upload new datasets (CSV)
- One-click model retraining
- Trend analysis & system intelligence

### 🔌 Developer API (Offline)
- Local REST API for integration into other apps
- Supports real-time hate/offensive detection
- Designed for social media platforms, chat systems, and moderation tools

---


---

## 4. How to Run the Project (Offline)

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- Windows / macOS / Linux
- Minimum **8 GB RAM** recommended

---

### Option A: One-Click Installation (Windows)

1. Double-click **`install.bat`**
2. The script will:
   - Create a Python virtual environment
   - Install backend dependencies
   - Install frontend dependencies
   - Build React frontend
   - Start the Flask backend

No internet is required after installation.

---

### Option B: Manual Setup (All Platforms)

#### Backend (Flask)
```bash

python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
python -m backend.app

cd frontend
npm install react-router-dom recharts
npm install axios
npm start