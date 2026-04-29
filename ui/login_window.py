import hashlib
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
QLineEdit, QPushButton, QDialog)
from PyQt6.QtCore import Qt
from Encryption.keygen import derive_key, generate_salt
from db.database import init_db, save_master_salt, get_master_salt, save_master_hash, get_master_hash
from server.local_server import set_session_key


class LoginWindow(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.attempts = 0
        self.max_attempts = 5
        self.setWindowTitle("Secure Password Manager")
        self.setFixedSize(420, 320)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.apply_theme()
        self.init_ui()

    def apply_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI';
            }
            QLineEdit {
                background-color: #2a2a3d;
                border: 1px solid #444466;
                border-radius: 6px;
                padding: 10px;
                color: #cdd6f4;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #7c6af7;
            }
            QPushButton {
                background-color: #7c6af7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9580ff;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        icon_label = QLabel("🔐")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px; background: transparent;")

        title = QLabel("Secure Password Manager")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #cdd6f4; background: transparent;")

        subtitle = QLabel("Enter your master password to unlock your vault")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 12px; color: #a6adc8; background: transparent;")

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Master password...")
        self.password_input.returnPressed.connect(self.handle_login)

        self.submit_btn = QPushButton("Unlock Vault")
        self.submit_btn.clicked.connect(self.handle_login)

        layout.addWidget(icon_label)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(self.password_input)
        layout.addWidget(self.submit_btn)

        self.setLayout(layout)

    def handle_login(self):
        password = self.password_input.text()

        if not password:
            self.show_warning("Password cannot be empty.")
            return

        init_db()
        salt = get_master_salt()

        if salt is None:
            salt = generate_salt()
            save_master_salt(salt)
            key = derive_key(password, salt)
            verification = hashlib.sha256(key).digest()
            save_master_hash(verification)
            set_session_key(key)
            self.on_success(key)
            self.close()
        else:
            key = derive_key(password, salt)
            verification = hashlib.sha256(key).digest()
            stored_hash = get_master_hash()
            if verification != stored_hash:
                self.attempts += 1
                remaining = self.max_attempts - self.attempts
                if self.attempts >= self.max_attempts:
                    self.show_warning("Maximum attempts reached. Application will now close.")
                    self.close()
                    return
                self.show_warning(f"Incorrect password. {remaining} attempt{'s' if remaining != 1 else ''} remaining.")
                self.password_input.clear()
                return
            set_session_key(key)
            self.on_success(key)
            self.close()

    def show_warning(self, message: str):
        warn = QDialog(self)
        warn.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        warn.setFixedSize(320, 160)
        warn.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                border: 1px solid #f38ba8;
                border-radius: 10px;
            }
            QWidget {
                background-color: #1e1e2e;
                font-family: 'Segoe UI';
            }
            QLabel {
                color: #cdd6f4;
            }
            QPushButton {
                background-color: #f38ba8;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff9eb5;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("⚠  WARNING")
        title.setStyleSheet("color: #f38ba8; font-size: 13px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet("font-size: 13px; color: #cdd6f4;")

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(warn.close)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(msg)
        layout.addLayout(btn_layout)
        warn.setLayout(layout)
        warn.exec()