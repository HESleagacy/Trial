import sqlite3
from datetime import datetime
from typing import Dict

DB_PATH = "backend/db.sqlite3" 

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_name TEXT NOT NULL,
            dose TEXT NOT NULL,
            frequency TEXT NOT NULL,
            advice TEXT NOT NULL,
            source TEXT NOT NULL,  -- ocr, manual, api
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            med_key TEXT NOT NULL,           -- e.g., "metformin 500mg"
            feedback_text TEXT NOT NULL,
            sentiment TEXT NOT NULL,         -- very_negative, negative, neutral, positive, very_positive
            source TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("DB is initialized: plans + feedback tables")

def save_plan(drug_name: str, dose: str, frequency: str, advice: str, source: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO plans (drug_name, dose, frequency, advice, source) VALUES (?, ?, ?, ?, ?)",
        (drug_name.lower(), dose, frequency, advice, source)
    )
    conn.commit()
    conn.close()

def save_feedback(med_key: str, feedback_text: str, sentiment: str, source: str):    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO feedback (med_key, feedback_text, sentiment, source) VALUES (?, ?, ?, ?)",
        (med_key.lower(), feedback_text, sentiment, source)
    )
    conn.commit()
    conn.close()

def get_dashboard_stats() -> Dict:    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT med_key, sentiment, source, COUNT(*) 
        FROM feedback 
        GROUP BY med_key, sentiment, source
    ''')
    rows = cursor.fetchall()
    stats = {}
    for med_key, sentiment, source, count in rows:
        if med_key not in stats:   #AGR MED_KEY PEHLE SE NA HO USE THIS LOOP
            stats[med_key] = {
                "very_negative": 0, "negative": 0, "neutral": 0,
                "positive": 0, "very_positive": 0,
                "sources": {}
            }
        stats[med_key][sentiment] += count
        stats[med_key]["sources"][source] = stats[med_key]["sources"].get(source, 0) + count
    
    conn.close()
    return stats
