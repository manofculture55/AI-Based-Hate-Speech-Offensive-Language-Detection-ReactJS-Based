import random
import sqlite3
import pandas as pd
from flask import Blueprint, request, jsonify
import os

# --- Blueprint ---
survey_bp = Blueprint("survey", __name__)

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DATA_DIR = os.path.join(BACKEND_DIR, "data")

DB_PATH = os.path.join(DATA_DIR, "app.db")
CSV_PATH = os.path.join(DATA_DIR, "clean_data.csv")


# ---------------------------
# Helper: Update CSV label
# ---------------------------
def update_label_in_csv(target_text, new_label):
    """
    Update truelabel of matching text in clean_data.csv.
    Runs ONLY after consensus is reached.
    """
    try:
        df = pd.read_csv(CSV_PATH)

        matches = df[df["text"] == target_text]
        if matches.empty:
            print("[Survey] Text not found in CSV, skipping update.")
            return

        df.loc[df["text"] == target_text, "truelabel"] = new_label
        df.to_csv(CSV_PATH, index=False)

        print(
            f"[Survey] CSV updated: '{target_text[:40]}...' → truelabel {new_label}"
        )

    except Exception as e:
        print(f"[Survey] CSV update failed: {e}")


# ---------------------------
# GET /survey/next
# ---------------------------
@survey_bp.route("/survey/next", methods=["GET"])
def get_next_survey_text():
    try:
        df = pd.read_csv(CSV_PATH)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT text FROM survey_corrections WHERE is_resolved = 1"
        )
        resolved_texts = {row[0] for row in cursor.fetchall()}
        conn.close()

        available = df[~df["text"].isin(resolved_texts)]

        if available.empty:
            return jsonify({"message": "No more texts available for survey"}), 200

        row = available.sample(1).iloc[0]

        return jsonify({
            "text": row["text"],
            "original_label": int(row["truelabel"])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
# POST /survey/submit
# ---------------------------
@survey_bp.route("/survey/submit", methods=["POST"])
def submit_survey_vote():
    data = request.json

    text = data.get("text")
    user_label = data.get("user_label")

    if text is None or user_label is None:
        return jsonify({"error": "Invalid payload"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT vote_trace, survey_count FROM survey_corrections WHERE text = ?",
        (text,)
    )
    row = cursor.fetchone()

    if row is None:
        cursor.execute("""
            INSERT INTO survey_corrections
            (text, original_label, survey_count, vote_trace)
            VALUES (?, ?, ?, ?)
        """, (text, user_label, 1, str(user_label)))
    else:
        vote_trace, survey_count = row
        new_trace = vote_trace + str(user_label)
        new_count = survey_count + 1

        cursor.execute("""
            UPDATE survey_corrections
            SET vote_trace = ?, survey_count = ?, updated_at = CURRENT_TIMESTAMP
            WHERE text = ?
        """, (new_trace, new_count, text))

        # --- Consensus check ---
        if new_trace.count(str(user_label)) >= 3:
            cursor.execute("""
                UPDATE survey_corrections
                SET resolved_label = ?, is_resolved = 1
                WHERE text = ?
            """, (user_label, text))

            # 🔁 Update CSV only after consensus
            update_label_in_csv(text, user_label)

    conn.commit()
    conn.close()

    return jsonify({"message": "Survey vote recorded successfully"}), 200
