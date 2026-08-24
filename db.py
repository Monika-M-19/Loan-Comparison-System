from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().with_name("loan_data.db")

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()


# ---------------- CREATE TABLE ----------------
def create_table():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loan_comparison (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_type TEXT,
        vehicle_type TEXT,
        amount REAL,
        years INTEGER,
        public_bank TEXT,
        private_bank TEXT,
        public_rate REAL,
        private_rate REAL,
        public_emi REAL,
        private_emi REAL,
        public_total REAL,
        private_total REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()


# ---------------- INSERT DATA ----------------
def insert_data(data):
    cursor.execute("""
    INSERT INTO loan_comparison (
        loan_type, vehicle_type, amount, years,
        public_bank, private_bank,
        public_rate, private_rate,
        public_emi, private_emi,
        public_total, private_total
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)

    conn.commit()


# ---------------- FETCH DATA ----------------
def fetch_rates():
    cursor.execute("""
    SELECT public_rate, private_rate FROM loan_comparison
    """)
    return cursor.fetchall()


def fetch_all():
    cursor.execute("""
    SELECT * FROM loan_comparison
    ORDER BY timestamp DESC, id DESC
    """)
    return cursor.fetchall()


def clear_history():
    cursor.execute("DELETE FROM loan_comparison")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'loan_comparison'")
    conn.commit()
