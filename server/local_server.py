from flask import Flask, request, jsonify
from flask_cors import CORS
from Encryption.vault import encrypt_password
from db.database import save_entry
from utils.password_gen import generate_password

app = Flask(__name__)
CORS(app)

session_key = None

def set_session_key(key: bytes):
    global session_key
    session_key = key

def clear_session_key():
    global session_key
    session_key = None

@app.route('/generate', methods=['POST'])
def generate():
    if session_key is None:
        return jsonify({"error": "vault is locked"}), 403

    data = request.json
    site = data.get("site", "unknown")
    username = data.get("username", "")

    password = generate_password()

    iv_site, enc_site = encrypt_password(site, session_key)
    iv_user, enc_user = encrypt_password(username, session_key)
    iv_pass, enc_pass = encrypt_password(password, session_key)

    save_entry(iv_site, enc_site, iv_user, enc_user, iv_pass, enc_pass)

    return jsonify({"password": password})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"locked": session_key is None})

def run_server():
    app.run(host='127.0.0.1', port=5000, debug=False)