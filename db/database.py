import sqlite3
import os

DB_PATH = "vault.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master (
            id INTEGER PRIMARY KEY,
            salt BLOB NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT NOT NULL,
            username TEXT NOT NULL,
            iv BLOB NOT NULL,
            ciphertext BLOB NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def save_master_salt(salt: bytes):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO master (salt) VALUES (?)", (salt,))
    conn.commit()
    conn.close()

def get_master_salt() -> bytes:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT salt FROM master LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def save_entry(site: str, username: str, iv: bytes, ciphertext: bytes):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO entries (site, username, iv, ciphertext) VALUES (?, ?, ?, ?)",
        (site, username, iv, ciphertext)
    )
    conn.commit()
    conn.close()

def get_entries():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, site, username, iv, ciphertext FROM entries")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_entry(entry_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()