import sqlite3
import datetime
import os

DB_PATH = "/app/data/history.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS summaries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  url TEXT, input_length INTEGER, summary TEXT, created_at TEXT)''')
    conn.commit()
    conn.close()

def save_log(url: str, text_len: int, summary: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO summaries (url, input_length, summary, created_at) VALUES (?, ?, ?, ?)",
              (url, text_len, summary, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()