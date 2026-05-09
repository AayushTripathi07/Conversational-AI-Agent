import sqlite3
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "leads.db")

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            platform TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def insert_lead(name: str, email: str, platform: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO leads (name, email, platform, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (name, email, platform, timestamp))
    conn.commit()
    conn.close()
    
def get_all_leads():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, platform, timestamp FROM leads ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    leads = []
    for r in rows:
        leads.append({
            "id": r[0],
            "name": r[1],
            "email": r[2],
            "platform": r[3],
            "timestamp": r[4]
        })
    return leads

# Initialize on import
create_tables()
