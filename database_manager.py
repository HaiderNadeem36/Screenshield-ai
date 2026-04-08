import sqlite3
import json

def init_db():
    conn = sqlite3.connect('wellbeing.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS journals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  text TEXT,
                  mood TEXT,
                  burnout INTEGER,
                  hours REAL,
                  suggestions TEXT)''')
    conn.commit()
    conn.close()

def add_entry(text, mood, burnout, hours, suggestions):
    conn = sqlite3.connect('wellbeing.db')
    c = conn.cursor()
    import time
    timestamp = time.strftime("%Y-%m-%d %I:%M %p")
    # Convert list of suggestions to JSON string for storage
    sug_json = json.dumps(suggestions)
    
    c.execute("INSERT INTO journals (date, text, mood, burnout, hours, suggestions) VALUES (?, ?, ?, ?, ?, ?)",
              (timestamp, text, mood, burnout, hours, sug_json))
    conn.commit()
    conn.close()

def get_all_entries():
    conn = sqlite3.connect('wellbeing.db')
    c = conn.cursor()
    c.execute("SELECT * FROM journals ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    
    entries = []
    for row in rows:
        entries.append({
            "id": row[0],
            "time": row[1],
            "text": row[2],
            "mood": row[3],
            "burnout": row[4],
            "screen_hours": row[5],
            "suggestions": json.loads(row[6])
        })
    return entries

def delete_entry(entry_id):
    conn = sqlite3.connect('wellbeing.db')
    c = conn.cursor()
    c.execute("DELETE FROM journals WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()
