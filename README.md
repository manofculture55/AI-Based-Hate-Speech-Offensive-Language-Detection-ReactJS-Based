# AI-Based Hate Speech & Offensive Language Detection  
**AI/ML Portfolio Project**  

**Execution Mode:** Fully Offline (No Internet, No External APIs)  
**Supported Languages:** English, Hindi, Hinglish (Code-Mixed)  
**Frontend:** React 19  
**Backend:** Flask 3 (Python 3.10)  
**Database:** SQLite  
**ML Stack:** scikit-learn, TensorFlow / Keras  
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

### Multilingual Intelligence
- Supports **English**, **Hindi**, and **Hinglish**
- Automatically detects language type
- Handles code-mixed and transliterated text

### AI & ML Models
- Classical ML: TF-IDF + Logistic Regression, SVM
- Deep Learning: BiLSTM (CPU optimized)
- Multiple models compared and analyzed
- Best-performing model used for inference

### Fully Offline & Secure
- No internet connection required
- No cloud APIs used
- All models, data, and logs stored locally
- Privacy-first design

### Fast & Efficient
- Average latency < **2 seconds**
- CPU-only execution
- Optimized inference pipeline

### Analytics & Insights
- Prediction history with pagination
- Class distribution charts
- Language distribution analysis
- Model accuracy comparison
- Confusion matrix & error analysis

### Human-in-the-Loop Learning
- Feedback system for correcting wrong predictions
- Survey system for collecting human labels
- Flag-word intelligence for identifying harmful terms
- Accuracy improves over time using real user input

### Hidden Admin Panel
- Secure, password-protected admin access
- Upload new datasets (CSV)
- One-click model retraining
- Trend analysis & system intelligence

### Developer API (Offline)
- Versioned REST API at `/api/v1` for integration into other apps
- Resource-oriented URLs, correct status codes, consistent JSON errors
- Supports real-time hate/offensive detection
- Designed for social media platforms, chat systems, and moderation tools

---

## 3. REST API

Full reference: **[backend/docs/API.md](backend/docs/API.md)**

Base path `/api/v1`. `GET /api/v1` returns a machine-readable index of every
endpoint; `GET /api/v1/health` reports whether the model is loaded.

```bash
curl -X POST http://127.0.0.1:5000/api/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"text": "you are stupid"}'
```

```json
{
  "id": 42,
  "label": 1,
  "label_name": "Offensive",
  "confidence": 0.8731,
  "probabilities": { "Normal": 0.0712, "Offensive": 0.8731, "Hate": 0.0557 },
  "language": "en",
  "model": "BiLSTM",
  "latency_ms": 118
}
```

| Resource | Endpoints |
|----------|-----------|
| Predictions | `POST/GET /predictions`, `GET/DELETE /predictions/{id}`, `GET /predictions/export` |
| Annotations | `POST/GET /annotations` |
| Flagged terms | `POST/GET /flagged-terms`, `DELETE /flagged-terms/{word}` |
| Analytics | `GET /analytics` and `/summary` `/trend` `/languages` `/models` `/dataset` `/errors` |
| Survey | `GET /survey/items/next`, `POST /survey/votes`, `GET /survey/stats` |
| Admin | `/admin/sessions`, `/admin/datasets`, `/admin/training-jobs`, `/admin/trends` |

The pre-v1 URLs (`/predict`, `/history`, `/analytics`, …) still work and return
their original response shapes, tagged with a `Deprecation` header. See the
mapping table in the API docs.

### Backend layout

```
backend/
  app.py                 Flask application factory
  wsgi.py                waitress entry point (production)
  src/
    api/v1/              HTTP layer, one module per resource
    api/                 auth, error envelope, pagination, schemas, serializers
    api/legacy.py        deprecated pre-v1 route shims
    services/            classifier, analytics, survey, datasets, training jobs
    repositories/        SQL
    utils/               config, paths, labels, db + migrations
```

---

## 4. How to Run the Project (Offline)

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- Windows / macOS / Linux
- Minimum **8 GB RAM** recommended

---

### Option A: Windows scripts

Setup runs **once**, then `run.bat` is the everyday entry point.

```bat
install.bat     :: first time only
run.bat         :: every time after that
```

**`install.bat`** creates the virtual environment, installs backend
dependencies, creates `.env` from `.env.example`, initializes and migrates the
SQLite database, normalizes the datasets, trains the models, installs frontend
dependencies, and finally offers to launch the app.

When it succeeds it writes a `.setup-complete` marker. Running it again detects
that marker and points you at `run.bat` instead of repeating several minutes of
work. It does **not** delete or rewrite itself — see the note below.

```bat
install.bat /repair    :: force a full re-install (new deps, broken venv)
```

**`run.bat`** starts the app:

| Command | Effect |
|---------|--------|
| `run.bat` | backend + frontend, each in its own window |
| `run.bat backend` | Flask development server only |
| `run.bat frontend` | React dev server only |
| `run.bat prod` | serve the API with waitress instead of Flask's dev server |

It refuses to start with a clear message if the venv or `node_modules` are
missing, and warns (rather than failing) when no trained model is present.

> **Why `install.bat` doesn't delete or comment itself out**
>
> Both are lossy and one is actively unsafe. `cmd.exe` reads a batch file from
> disk *as it executes*, line by line — a script that rewrites itself mid-run
> can have the interpreter resume at the wrong byte offset, so the behaviour is
> genuinely undefined. And deleting the installer means the next time you need
> it — new dependency, corrupted venv, fresh machine — it is gone. The marker
> file gives the same "install once, then just run" experience while keeping
> repair possible and the setup steps readable as documentation.

No internet is required after installation.

---

### Option B: Manual Setup (All Platforms)

#### Backend (Flask)
```bash
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # macOS/Linux

pip install -r requirements.txt
# or, for an exactly reproducible environment:
# pip install -r requirements.lock.txt

copy .env.example .env      # Windows
# cp .env.example .env      # macOS/Linux

python -m backend.src.utils.db          # create / migrate the database
python -m backend.src.data.normalize    # build clean_data.csv (first run)
python -m backend.src.training.train    # train the models (first run)

python -m backend.app       # development server on :5000
# python -m backend.wsgi    # waitress, for anything beyond local dev
```

#### Frontend (React)
```bash
cd frontend
npm install
cp .env.example .env        # optional; the client defaults to localhost:5000
npm start
```

---

## 5. Configuration

Backend settings come from `.env` (see `.env.example` for the full list):

| Variable | Default | Purpose |
|----------|---------|---------|
| `HSD_API_KEY` | `dev-api-key-change-me` | value clients send as `X-API-KEY` |
| `HSD_ADMIN_KEY` | `dev-admin-key-change-me` | value for `X-ADMIN-KEY` |
| `HSD_ADMIN_PASSWORD` | `admin123` | verified server-side at admin login |
| `HSD_CORS_ORIGINS` | `localhost:3000,127.0.0.1:3000` | allowed browser origins |
| `HSD_ENABLE_LEGACY_ROUTES` | `1` | serve the deprecated pre-v1 URLs |

> The shipped defaults are public — they are in this repository. Change them
> before exposing the app to anyone else. The server prints a startup warning
> for as long as they are unchanged.

The frontend reads `REACT_APP_API_BASE_URL` from `frontend/.env`.

---

## 6. Tests

```bash
cd frontend && npm test        # React component tests
```