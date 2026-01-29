import sqlite3
import os

# Absolute path to backend/data/app.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DATA_DIR = os.path.join(BACKEND_DIR, "data")

DB_PATH = os.path.join(DATA_DIR, "app.db")


def init_db():
    """
    Initializes the SQLite database with the mandatory schema.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            lang TEXT CHECK(lang IN ('hi','en','hi-en')),
            predicted_label INTEGER CHECK(predicted_label IN (0,1,2)),
            score REAL NOT NULL,
            model_name TEXT NOT NULL,
            latency_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT,
            macro_f1 REAL,
            accuracy REAL,
            precision REAL,
            recall REAL,
            latency_p95_ms REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS annotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            lang TEXT,
            truelabel INTEGER,
            source TEXT
        )
    ''')

    conn.commit()
    conn.close()

    print(f"✅ Database initialized successfully at: {DB_PATH}")


if __name__ == "__main__":
    init_db()
