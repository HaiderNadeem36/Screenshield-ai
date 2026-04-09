import sqlite3
import json
import pandas as pd

# ─────────────────────────────────────────────
# DATABASE INITIALISATION
# Creates two tables:
#   journals   — stores every user journal entry with mood and suggestions
#   suggestions — stores all age-appropriate mental health suggestions
#                 loaded once from knowledge_base.csv on first launch
# ─────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect('wellbeing.db')
    c = conn.cursor()

    # Journal entries table — burnout and screen_hours removed (out of scope)
    c.execute('''CREATE TABLE IF NOT EXISTS journals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  text TEXT,
                  mood TEXT,
                  suggestions TEXT)''')

    # Suggestions table — queried by mood + age_group at runtime
    # Replaces CSV file-based lookup for consistency and reliability
    c.execute('''CREATE TABLE IF NOT EXISTS suggestions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  mood TEXT,
                  age_group TEXT,
                  suggestion_text TEXT)''')

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# KNOWLEDGE BASE INITIALISATION
# Reads knowledge_base.csv once on first launch
# and populates the suggestions table in SQLite.
# Skips if table is already populated (idempotent).
# mood values:      High, Medium, Low
# age_group values: 15-25, 26-40, 41-65
# ─────────────────────────────────────────────

def init_knowledge_base():
    conn = sqlite3.connect('wellbeing.db')
    c = conn.cursor()

    # Check if suggestions table is already populated
    c.execute("SELECT COUNT(*) FROM suggestions")
    count = c.fetchone()[0]

    if count == 0:
        # Load CSV and insert all rows into SQLite — runs only once
        try:
            df = pd.read_csv('knowledge_base.csv')
            for _, row in df.iterrows():
                c.execute(
                    "INSERT INTO suggestions (mood, age_group, suggestion_text) VALUES (?, ?, ?)",
                    (row['mood'], row['age_group'], row['suggestion_text'])
                )
            conn.commit()
        except Exception as e:
            print(f"Knowledge base load error: {e}")

    conn.close()


# ─────────────────────────────────────────────
# SUGGESTION RETRIEVAL
# Fetches one random suggestion from SQLite
# filtered by predicted mood and user age group.
# This replaces the fragile CSV keyword-matching system.
# mood      — predicted by Naive Bayes: High, Medium, Low
# age_group — derived from user age at session start
# ─────────────────────────────────────────────

def get_suggestion(mood, age_group):
    conn = sqlite3.connect('wellbeing.db')
    c = conn.cursor()

    c.execute(
        "SELECT suggestion_text FROM suggestions WHERE mood=? AND age_group=? ORDER BY RANDOM() LIMIT 1",
        (mood, age_group)
    )
    row = c.fetchone()
    conn.close()

    # Fallback — should never trigger if KB is properly loaded
    if row:
        return row[0]
    return "Take a moment to breathe and be kind to yourself today."


# ─────────────────────────────────────────────
# JOURNAL ENTRY — ADD
# Saves a new journal entry to the journals table.
# suggestions stored as JSON string for flexibility.
# ─────────────────────────────────────────────

def add_entry(text, mood, suggestions):
    conn = sqlite3.connect('wellbeing.db')
    c = conn.cursor()

    import time
    timestamp = time.strftime("%Y-%m-%d %I:%M %p")

    # Store suggestion list as JSON string
    sug_json = json.dumps(suggestions)

    c.execute(
        "INSERT INTO journals (date, text, mood, suggestions) VALUES (?, ?, ?, ?)",
        (timestamp, text, mood, sug_json)
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# JOURNAL ENTRIES — FETCH ALL
# Returns all journal entries ordered newest first.
# Used by sidebar history and trends tab.
# ─────────────────────────────────────────────

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
            "suggestions": json.loads(row[4])
        })
    return entries


# ─────────────────────────────────────────────
# JOURNAL ENTRY — DELETE
# Removes a single entry by ID from the database.
# Called from sidebar history delete button.
# ─────────────────────────────────────────────

def delete_entry(entry_id):
    conn = sqlite3.connect('wellbeing.db')
    c = conn.cursor()
    c.execute("DELETE FROM journals WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()
