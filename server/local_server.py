from flask import Flask, request, jsonify
from flask_cors import CORS
from Encryption.vault import encrypt
from db.database import save_entry
from utils.password_gen import generate_password

app = Flask(__name__)
CORS(app)

session_key = None
session_vault_id = None

def set_session_key(key: bytes):
    global session_key
    session_key = key

def clear_session_key():
    global session_key, session_vault_id
    session_key = None
    session_vault_id = None

def set_session_vault(vault_id: int):
    global session_vault_id
    session_vault_id = vault_id

def clear_session_vault():
    global session_vault_id
    session_vault_id = None

@app.route('/generate', methods=['POST'])
def generate():
    if session_key is None:
        return jsonify({"error": "vault is locked"}), 403
    elif session_vault_id is None:
        return jsonify({"error": "no vault open"}), 403

    data = request.json
    site = data.get("site", "unknown")
    username = data.get("username", "")

    password = generate_password()

    result = encrypt([site, username, password], session_key)
    iv_site, enc_site = result[0]
    iv_user, enc_user = result[1]
    iv_pass, enc_pass = result[2]


    save_entry(session_vault_id, iv_site, enc_site, iv_user, enc_user, iv_pass, enc_pass)

    return jsonify({"password": password})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"locked": session_key is None})

def run_server():
    app.run(host='127.0.0.1', port=5000, debug=False)
