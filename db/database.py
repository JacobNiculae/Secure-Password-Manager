import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "vault.db")

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
        CREATE TABLE IF NOT EXISTS vaults (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            iv_name BLOB NOT NULL,
            enc_name BLOB NOT NULL,
            salt BLOB,
            hash BLOB
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vault_id INTEGER NOT NULL DEFAULT 0,
            iv_site BLOB NOT NULL,
            enc_site BLOB NOT NULL,
            iv_username BLOB NOT NULL,
            enc_username BLOB NOT NULL,
            iv_password BLOB NOT NULL,
            enc_password BLOB NOT NULL
        )
    ''')

    # Migration: add vault_id to pre-existing entries table
    cursor.execute("PRAGMA table_info(entries)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'vault_id' not in columns:
        cursor.execute("ALTER TABLE entries ADD COLUMN vault_id INTEGER DEFAULT 0")

    # Migration: add salt/hash to pre-existing vaults table
    cursor.execute("PRAGMA table_info(vaults)")
    vault_columns = [col[1] for col in cursor.fetchall()]
    if 'salt' not in vault_columns:
        cursor.execute("ALTER TABLE vaults ADD COLUMN salt BLOB")
    if 'hash' not in vault_columns:
        cursor.execute("ALTER TABLE vaults ADD COLUMN hash BLOB")

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

def create_vault(iv_name: bytes, enc_name: bytes, salt: bytes, hash_value: bytes) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO vaults (iv_name, enc_name, salt, hash) VALUES (?, ?, ?, ?)",
        (iv_name, enc_name, salt, hash_value)
    )
    vault_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return vault_id

def get_vaults():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, iv_name, enc_name FROM vaults")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_vault_auth(vault_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT salt, hash FROM vaults WHERE id = ?", (vault_id,))
    row = cursor.fetchone()
    conn.close()
    return row if row else (None, None)

def delete_vault(vault_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries WHERE vault_id = ?", (vault_id,))
    cursor.execute("DELETE FROM vaults WHERE id = ?", (vault_id,))
    conn.commit()
    conn.close()

def get_entry_count(vault_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM entries WHERE vault_id = ?", (vault_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def has_legacy_entries() -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM entries WHERE vault_id = 0")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def assign_legacy_entries(vault_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE entries SET vault_id = ? WHERE vault_id = 0", (vault_id,))
    conn.commit()
    conn.close()

def save_entry(vault_id: int, iv_site, enc_site, iv_username, enc_username, iv_password, enc_password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO entries (vault_id, iv_site, enc_site, iv_username, enc_username, iv_password, enc_password) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (vault_id, iv_site, enc_site, iv_username, enc_username, iv_password, enc_password)
    )
    conn.commit()
    conn.close()

def get_entries(vault_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, iv_site, enc_site, iv_username, enc_username, iv_password, enc_password FROM entries WHERE vault_id = ?",
        (vault_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_entry(entry_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
