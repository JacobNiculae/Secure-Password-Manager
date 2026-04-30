import sqlite3

DB_PATH = "vault.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master (
            id INTEGER PRIMARY KEY,
            salt BLOB NOT NULL,
            hash BLOB
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            iv_site BLOB NOT NULL,
            enc_site BLOB NOT NULL,
            iv_username BLOB NOT NULL,
            enc_username BLOB NOT NULL,
            iv_password BLOB NOT NULL,
            enc_password BLOB NOT NULL
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

def save_master_hash(hash_value: bytes):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE master SET hash = ?", (hash_value,))
    conn.commit()
    conn.close()

def get_master_hash() -> bytes:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT hash FROM master LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def save_entry(iv_site, enc_site, iv_username, enc_username, iv_password, enc_password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO entries (iv_site, enc_site, iv_username, enc_username, iv_password, enc_password) VALUES (?, ?, ?, ?, ?, ?)",
        (iv_site, enc_site, iv_username, enc_username, iv_password, enc_password)
    )
    conn.commit()
    conn.close()

def get_entries():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, iv_site, enc_site, iv_username, enc_username, iv_password, enc_password FROM entries")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_entry(entry_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()