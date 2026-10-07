import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'greencode.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                language TEXT NOT NULL,
                original_code TEXT NOT NULL,
                optimized_code TEXT NOT NULL,
                original_eco_score INTEGER NOT NULL,
                optimized_eco_score INTEGER NOT NULL,
                original_joules REAL NOT NULL,
                optimized_joules REAL NOT NULL,
                carbon_saved_pct REAL NOT NULL,
                speedup_factor REAL NOT NULL,
                issue_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def save_audit(project_name, language, original_code, optimized_code,
               orig_score, opt_score, orig_joules, opt_joules,
               carbon_saved_pct, speedup_factor, issue_count):
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audits (
                project_name, language, original_code, optimized_code,
                original_eco_score, optimized_eco_score, original_joules, optimized_joules,
                carbon_saved_pct, speedup_factor, issue_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project_name, language, original_code, optimized_code,
            orig_score, opt_score, orig_joules, opt_joules,
            carbon_saved_pct, speedup_factor, issue_count,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return cursor.lastrowid

def delete_audit(audit_id):
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM audits WHERE id = ?', (audit_id,))
        conn.commit()
        return cursor.rowcount > 0

def clear_all_audits():
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM audits')
        conn.commit()
        return True

def get_all_audits(limit=20):
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM audits ORDER BY id DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_audit_by_id(audit_id):
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM audits WHERE id = ?', (audit_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_sustainability_stats():
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total_audits,
                COALESCE(SUM(original_joules - optimized_joules), 0) as total_joules_saved,
                COALESCE(AVG(carbon_saved_pct), 0) as avg_carbon_reduced_pct,
                COALESCE(AVG(speedup_factor), 1.0) as avg_speedup
            FROM audits
        ''')
        row = cursor.fetchone()
        stats = dict(row)
        # Calculate total gCO2e saved (Joules saved * 0.000132)
        stats["total_gco2e_saved"] = round(stats["total_joules_saved"] * 0.000132, 6)
        stats["total_joules_saved"] = round(stats["total_joules_saved"], 4)
        stats["avg_carbon_reduced_pct"] = round(stats["avg_carbon_reduced_pct"], 1)
        stats["avg_speedup"] = round(stats["avg_speedup"], 2)
        return stats
