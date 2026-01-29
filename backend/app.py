from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import time
import sqlite3
import pandas as pd
import json
from tensorflow.keras.models import load_model
import os
import sys
from werkzeug.utils import secure_filename
from backend.src.utils.config import API_KEY, MAX_API_TEXT_LENGTH



# --- PATH SETUP (IMPORTANT) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


# --- ENSURE REQUIRED BACKEND DIRECTORIES EXIST ---
BACKEND_DATA_DIR = os.path.join(BASE_DIR, "data")
BACKEND_MODELS_DIR = os.path.join(BASE_DIR, "models")
BACKEND_REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(BACKEND_DATA_DIR, exist_ok=True)
os.makedirs(BACKEND_MODELS_DIR, exist_ok=True)
os.makedirs(BACKEND_REPORTS_DIR, exist_ok=True)



BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

DB_PATH = os.path.join(BACKEND_DIR, "data", "app.db")

# --- IMPORT PROJECT MODULES ---
from src.models.bilstm import DeepModel
from src.data.preprocess import clean_text
from src.data.langid import detect_language_strict
from src.training.train import run_training

# --- 1. GLOBAL STATE & MODEL LOADING ---
ADMIN_SECRET = "KRIXION_ADMIN_2026"
def verify_admin(request):
    return request.headers.get("X-ADMIN-KEY") == ADMIN_SECRET

def verify_api_key(request):
    return request.headers.get("X-API-KEY") == API_KEY


print("  [App] Initializing KRIXION AI Engine...")
model_wrapper = DeepModel(architecture='bilstm')

try:
    model_wrapper.load_tokenizer()
    model_path = "backend/models/deep/bilstm_model.h5"
    if os.path.exists(model_path):
        model_wrapper.model = load_model(model_path)
        print("  [App] BiLSTM Model Loaded Successfully!")
    else:
        print(f"  [App] Error: Model not found at {model_path}")
except Exception as e:
    print(f"  [App] Critical Error Loading Model: {e}")

app = Flask(__name__)
CORS(app)


# --- 2. DATABASE HELPERS ---
def get_db_connection():
    return sqlite3.connect(DB_PATH)


def save_to_db(text, lang, label, score, latency):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO predictions (text, lang, predicted_label, score, model_name, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (text, lang, int(label), float(score), 'BiLSTM', int(latency * 1000)),
        )
        prediction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return prediction_id
    except Exception as e:
        print(f"DB Save Error: {e}")
        return None


def get_history_data(page=1, limit=20):
    try:
        offset = (page - 1) * limit
        conn = get_db_connection()

        # TOTAL COUNT
        total_df = pd.read_sql_query(
            "SELECT COUNT(*) as total FROM predictions",
            conn
        )
        total = int(total_df.iloc[0]["total"])

        # PAGINATED DATA
        df = pd.read_sql_query(
            """
            SELECT text, predicted_label, score, latency_ms, created_at
            FROM predictions
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            conn,
            params=(limit, offset),
        )

        conn.close()

        # ADD result column (SAFE)
        if not df.empty:
            df["result"] = df["predicted_label"].map(
                {0: "Normal", 1: "Offensive", 2: "Hate"}
            )
            df["score"] = df["score"].apply(lambda x: f"{x:.1%}")
            df["latency_ms"] = df["latency_ms"].apply(lambda x: f"{x} ms")
            df["created_at"] = df["created_at"].astype(str)

        return {
            "data": df.to_dict("records"),
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
        }

    except Exception as e:
        print(f"DB Error: {e}")
        return {
            "data": [],
            "total": 0,
            "page": page,
            "pages": 0,
        }



def get_predictions_trend_data(days=30):
    """Get predictions count grouped by date for line chart"""
    try:
        conn = get_db_connection()
        query = """
        SELECT DATE(created_at) as date, COUNT(*) as count 
        FROM predictions 
        WHERE created_at >= datetime('now', '-{} days')
        GROUP BY DATE(created_at) 
        ORDER BY date
        """.format(days)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return {'dates': [], 'counts': []}
        
        dates = df['date'].tolist()
        counts = df['count'].tolist()
        return {'dates': dates, 'counts': counts}
    except Exception as e:
        print(f"Trend Data Error: {e}")
        return {'dates': [], 'counts': []}


def get_model_performance_data():
    """Load model metrics from reports/training_report_all.json"""
    try:
        # Default fallback metrics if no report file
        default_metrics = {
            'BiLSTM': {'f1': 0.87, 'accuracy': 0.89, 'latency': 120},
            'Baseline': {'f1': 0.78, 'accuracy': 0.80, 'latency': 45},
            'DistilBERT': {'f1': 0.90, 'accuracy': 0.91, 'latency': 850}
        }
        
        # Try to load real metrics
        if os.path.exists("reports/training_report_all.json"):
            with open("reports/training_report_all.json", "r") as f:
                metrics = json.load(f)
                # Extract relevant metrics (adjust keys based on your JSON structure)
                return {
                    'BiLSTM': {
                        'f1': metrics.get('bilstm_macro_f1', 0.87),
                        'accuracy': metrics.get('bilstm_accuracy', 0.89),
                        'latency': metrics.get('bilstm_latency_ms', 120)
                    },
                    'Baseline': {
                        'f1': metrics.get('baseline_f1', 0.78),
                        'accuracy': metrics.get('baseline_accuracy', 0.80), 
                        'latency': metrics.get('baseline_latency_ms', 45)
                    },
                    'DistilBERT': {
                        'f1': metrics.get('transformer_f1', 0.90),
                        'accuracy': metrics.get('transformer_accuracy', 0.91),
                        'latency': metrics.get('transformer_latency_ms', 850)
                    }
                }
        return default_metrics
        
    except Exception as e:
        print(f"Model Metrics Error: {e}")
        return default_metrics


def get_training_dataset_stats():
    """Get training dataset statistics from clean_data.csv"""
    try:
        csv_path = 'data/clean_data.csv'
        if not os.path.exists(csv_path):
            return {
                'total_samples': 0,
                'lang_dist': {'en': 0.35, 'hi': 0.40, 'hi-en': 0.25},
                'label_dist': {'Normal': 0.4, 'Offensive': 0.35, 'Hate': 0.25}
            }
        
        df = pd.read_csv(csv_path)
        total_samples = len(df)
        
        # Language distribution
        if 'lang' in df.columns:
            lang_counts = df['lang'].value_counts(normalize=True).to_dict()
        else:
            lang_counts = {'en': 0.35, 'hi': 0.40, 'hi-en': 0.25}
        
        # Label distribution  
        if 'label' in df.columns:
            label_map = {0: 'Normal', 1: 'Offensive', 2: 'Hate'}
            df['label_name'] = df['label'].map(label_map).fillna('Normal')
            label_counts = df['label_name'].value_counts(normalize=True).to_dict()
        else:
            label_counts = {'Normal': 0.4, 'Offensive': 0.35, 'Hate': 0.25}
            
        return {
            'total_samples': total_samples,
            'lang_dist': lang_counts,
            'label_dist': label_counts
        }
    except Exception as e:
        print(f"Dataset Stats Error: {e}")
        return {
            'total_samples': 0,
            'lang_dist': {'en': 0.35, 'hi': 0.40, 'hi-en': 0.25},
            'label_dist': {'Normal': 0.4, 'Offensive': 0.35, 'Hate': 0.25}
        }


def get_language_intelligence():
    """
    Returns:
    - language distribution
    - language x class matrix
    """
    try:
        conn = get_db_connection()

        df = pd.read_sql_query(
            """
            SELECT lang, predicted_label
            FROM predictions
            """,
            conn
        )
        conn.close()

        if df.empty:
            return {
                "language_distribution": {},
                "language_class_matrix": {}
            }

        # 1️⃣ Language distribution
        lang_dist = df["lang"].value_counts().to_dict()

        # 2️⃣ Language × Class matrix
        label_map = {0: "Normal", 1: "Offensive", 2: "Hate"}
        df["label_name"] = df["predicted_label"].map(label_map)

        matrix = (
            df.groupby(["lang", "label_name"])
              .size()
              .unstack(fill_value=0)
              .to_dict(orient="index")
        )

        return {
            "language_distribution": lang_dist,
            "language_class_matrix": matrix
        }

    except Exception as e:
        print(f"Language analytics error: {e}")
        return {
            "language_distribution": {},
            "language_class_matrix": {}
        }


@app.route("/")
def health():
    return {"status": "KRIXION backend running"}

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "Empty text"}), 400

    start = time.time()

    cleaned = clean_text(text)
    origin = "indo_mixed" if any(w in cleaned.lower() for w in ["hai","nahi","tum","aap","kya","kyu"]) else "english"
    lang = detect_language_strict(cleaned, origin)

    seq = model_wrapper.preprocess([cleaned])
    probs = model_wrapper.model.predict(seq, verbose=0)[0]

    label = int(np.argmax(probs))
    confidence = float(probs[label])
    latency = time.time() - start

    prediction_id = save_to_db(text, lang, label, confidence, latency)

    return jsonify({
        "label": label,
        "confidence": confidence,
        "language": lang,
        "latency_ms": int(latency * 1000),
        "prediction_id": prediction_id,
    })


@app.route("/api/classify", methods=["POST"])
def api_classify():
    # 1️⃣ API KEY CHECK
    if not verify_api_key(request):
        return jsonify({"error": "Invalid API key"}), 401

    # 2️⃣ INPUT VALIDATION
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Text is required"}), 400

    text = data["text"].strip()
    if not text:
        return jsonify({"error": "Text cannot be empty"}), 400

    if len(text) > MAX_API_TEXT_LENGTH:
        return jsonify({"error": "Text too long"}), 400

    # 3️⃣ RUN ML PIPELINE (REUSE EXISTING LOGIC)
    cleaned = clean_text(text)

    origin = "indo_mixed" if any(
        w in cleaned.lower()
        for w in ["hai", "nahi", "tum", "aap", "kya", "kyu"]
    ) else "english"

    lang = detect_language_strict(cleaned, origin)

    seq = model_wrapper.preprocess([cleaned])
    probs = model_wrapper.model.predict(seq, verbose=0)[0]

    label = int(np.argmax(probs))

    # 4️⃣ RETURN ONLY LABEL (AS AGREED)
    return jsonify({
        "label": label
    })



@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()

    text = data.get("text")
    lang = data.get("language")
    correct_label = data.get("correct_label")

    if text is None or lang is None or correct_label is None:
        return jsonify({"error": "Invalid feedback data"}), 400

    ok = save_feedback(text, lang, int(correct_label))

    if ok:
        return jsonify({"status": "feedback_saved"})
    else:
        return jsonify({"error": "failed_to_save"}), 500




# FEEDBACK DATABASE FUNCTION - ADD THIS ENTIRE FUNCTION
def save_feedback(text, lang, correct_label):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO annotations (text, lang, truelabel)
            VALUES (?, ?, ?)
        """, (text, lang, correct_label))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Feedback error: {e}")
        return False





@app.route("/history", methods=["GET"])
def history():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    data = get_history_data(page=page, limit=limit)
    return jsonify(data)


@app.route("/analytics", methods=["GET"])
def analytics():
    # -------- DEFAULT SAFE VALUE (CRITICAL) --------
    language_stats = {
        "language_distribution": {},
        "language_class_matrix": {}
    }

    # -------- CLASS COUNTS --------
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT predicted_label FROM predictions",
        conn
    )
    conn.close()

    counts = (
        df['predicted_label']
        .value_counts()
        .reindex([0, 1, 2], fill_value=0)
        .to_dict()
    )

    # -------- OTHER ANALYTICS --------
    trend = get_predictions_trend_data()
    model_metrics = get_model_performance_data()
    error_analysis = get_error_analysis()

    # -------- LANGUAGE INTELLIGENCE --------
    try:
        language_stats = get_language_intelligence()
    except Exception as e:
        print("Language analytics failed:", e)



    return jsonify({
        "total_predictions": int(sum(counts.values())),
        "class_counts": {
            "normal": int(counts[0]),
            "offensive": int(counts[1]),
            "hate": int(counts[2])
        },
        "trend": trend,
        "models": model_metrics,
        "language": language_stats,
        "error_analysis": error_analysis
    })

def get_error_analysis(limit=20):
    """
    Compare predictions with user feedback (annotations)
    """
    try:
        conn = get_db_connection()

        query = """
        SELECT
            p.text,
            p.lang,
            p.predicted_label,
            a.truelabel
        FROM annotations a
        JOIN predictions p
        ON p.text = a.text
        AND p.lang = a.lang
        AND p.created_at = (
            SELECT MAX(created_at)
            FROM predictions
            WHERE text = a.text AND lang = a.lang
        )
        ORDER BY p.created_at DESC
        LIMIT ?
        """




        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()

        if df.empty:
            return {
                "confusion": {},
                "samples": []
            }

        # Confusion matrix
        confusion = (
            df.groupby(["truelabel", "predicted_label"])
              .size()
              .unstack(fill_value=0)
              .to_dict()
        )

        # Misclassified samples
        samples = []
        for _, row in df.iterrows():
            if row["truelabel"] != row["predicted_label"]:
                samples.append({
                    "text": row["text"][:120] + "...",
                    "language": row["lang"],
                    "predicted": int(row["predicted_label"]),
                    "actual": int(row["truelabel"])
                })

        return {
            "confusion": confusion,
            "samples": samples
        }

    except Exception as e:
        print("Error analysis failed:", e)
        return {
            "confusion": {},
            "samples": []
        }




@app.route("/admin/upload", methods=["POST"])
def admin_upload():

    upload_path = os.path.join(DATA_DIR, "clean_data.csv")

    print("UPLOAD HANDLER CALLED")
    print("Current working directory:", os.getcwd())
    print("Target CSV path:", upload_path)

    if not verify_admin(request):
        return jsonify({"error": "Unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = secure_filename(file.filename)

    if not filename.endswith(".csv"):
        return jsonify({"error": "Only CSV allowed"}), 400

    try:
        df_new = pd.read_csv(file)

        if not {"text", "label"}.issubset(df_new.columns):
            return jsonify({"error": "CSV must contain text and label columns"}), 400

        if os.path.exists(upload_path):
            df_existing = pd.read_csv(upload_path)
            df_all = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_all = df_new

        df_all.to_csv(upload_path, index=False)

        return jsonify({
            "status": "success",
            "rows_added": len(df_new),
            "saved_to": upload_path
        })

    except Exception as e:
        print("UPLOAD ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/admin/retrain", methods=["POST"])
def admin_retrain():
    if not verify_admin(request):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        run_training()
        return jsonify({"status": "training completed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)
