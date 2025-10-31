import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Dict
from contextlib import contextmanager

# Use relative path that works in Docker/prod
DB_PATH = Path(__file__).parent / "db.sqlite3"

@contextmanager
def get_db():
    """Context manager for thread-safe DB connections."""
    conn = sqlite3.connect(
        DB_PATH, 
        check_same_thread=False,  # Required for FastAPI async
        timeout=10.0              # Prevent deadlocks
    )
    conn.row_factory = sqlite3.Row  # Dict-like rows
    try:
        yield conn
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize tables + indexes."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_name TEXT NOT NULL,
                dose TEXT NOT NULL,
                frequency TEXT NOT NULL,
                advice TEXT NOT NULL,
                source TEXT NOT NULL CHECK(source IN ('manual', 'ocr', 'api')),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(drug_name, dose, frequency, source)
            )
        ''')
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                med_key TEXT NOT NULL,
                feedback_text TEXT NOT NULL,
                sentiment TEXT NOT NULL CHECK(sentiment IN (
                    'very_negative', 'negative', 'neutral', 
                    'positive', 'very_positive'
                )),
                source TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_med ON feedback(med_key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_sentiment ON feedback(sentiment)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_plans_drug ON plans(drug_name)')
        
        conn.commit()
        print(f"DB initialized at {DB_PATH.absolute()}: plans + feedback tables + indexes")

def save_plan(drug_name: str, dose: str, frequency: str, advice: str, source: str):
    """Save AI plan with error handling."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO plans (drug_name, dose, frequency, advice, source) "
                "VALUES (?, ?, ?, ?, ?)",
                (drug_name.lower().strip(), dose.strip(), frequency.strip(), advice, source)
            )
            conn.commit()
            print(f"Saved plan: {drug_name} {dose} ({source})")
    except sqlite3.IntegrityError:
        print(f"Plan already exists: {drug_name} {dose}")
    except Exception as e:
        print(f"DB Error saving plan: {e}")
        raise

def save_feedback(med_key: str, feedback_text: str, sentiment: str, source: str):
    """Save feedback with validation."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feedback (med_key, feedback_text, sentiment, source) "
                "VALUES (?, ?, ?, ?)",
                (med_key.lower().strip(), feedback_text.strip(), sentiment, source)
            )
            conn.commit()
            print(f"Saved feedback: {med_key} ({sentiment})")
    except sqlite3.IntegrityError as e:
        print(f"Feedback validation failed: {e}")
    except Exception as e:
        print(f"DB Error saving feedback: {e}")
        raise

def get_dashboard_stats() -> Dict:
    """Get aggregated feedback stats for dashboard."""
    stats = {}
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    med_key, 
                    sentiment, 
                    source, 
                    COUNT(*) as count
                FROM feedback 
                GROUP BY med_key, sentiment, source
                ORDER BY med_key, count DESC
            ''')
            
            rows = cursor.fetchall()
            
            for med_key, sentiment, source, count in rows:
                if med_key not in stats:
                    stats[med_key] = {
                        "very_negative": 0, 
                        "negative": 0, 
                        "neutral": 0,
                        "positive": 0, 
                        "very_positive": 0,
                        "sources": {}
                    }
                
                # Aggregate sentiment counts
                if sentiment in stats[med_key]:
                    stats[med_key][sentiment] += count
                
                # Aggregate sources
                stats[med_key]["sources"][source] = (
                    stats[med_key]["sources"].get(source, 0) + count
                )
            
            print(f"Dashboard stats: {len(stats)} medications")
            return stats
            
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        return {}

# Migration helper
def migrate_old_data():
    """Run once to fix existing data."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            # Add indexes if missing
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_med ON feedback(med_key)")
            conn.commit()
        print(" Migration complete")
    except Exception as e:
        print(f" Migration failed: {e}")
