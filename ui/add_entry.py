from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
QLineEdit, QPushButton, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt
from Encryption.vault import encrypt_password, decrypt_password
from db.database import save_entry, delete_entry
from utils.password_gen import generate_password

DARK = {
    "bg": "#1e1e2e",
    "surface": "#2a2a3d",
    "accent": "#7c6af7",
    "text": "#cdd6f4",
    "subtext": "#a6adc8",
}

class AddEntryDialog(QDialog):
    def __init__(self, key: bytes, vault_id: int, parent=None, entry=None):
        super().__init__(parent)
        self.key = key
        self.vault_id = vault_id
        self.entry = entry
        self.setWindowTitle("Edit Entry" if entry else "Add New Entry")
        self.setFixedSize(420, 340)
        self.apply_theme()
        self.init_ui()
        if entry:
            self.populate_fields()

    def apply_theme(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DARK['bg']};
                border-radius: 12px;
            }}
            QWidget {{
                background-color: {DARK['bg']};
                color: {DARK['text']};
                font-family: 'Segoe UI';
                font-size: 13px;
            }}
            QLineEdit {{
                background-color: {DARK['surface']};
                border: 1px solid #33334d;
                border-radius: 6px;
                padding: 8px 10px;
                color: {DARK['text']};
            }}
            QLineEdit:focus {{
                border: 1px solid {DARK['accent']};
            }}
            QPushButton {{
                background-color: {DARK['surface']};
                color: {DARK['text']};
                border: 1px solid #33334d;
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: {DARK['accent']};
                color: white;
                border: 1px solid {DARK['accent']};
            }}
            QLabel {{
                color: {DARK['subtext']};
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }}
            QCheckBox {{
                color: {DARK['text']};
            }}
            QLineEdit#length_input {{
                background-color: {DARK['surface']};
                border: 1px solid #33334d;
                border-radius: 6px;
                padding: 4px 8px;
                color: {DARK['text']};
                max-width: 45px;
            }}
        """)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(24, 24, 24, 24)

        self.site_input = QLineEdit()
        self.site_input.setPlaceholderText("e.g. google.com")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username or email")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        gen_layout = QHBoxLayout()
        gen_layout.setSpacing(8)

        self.length_input = QLineEdit()
        self.length_input.setObjectName("length_input")
        self.length_input.setText("20")
        self.length_input.setFixedWidth(45)

        self.symbols_check = QCheckBox("Symbols")
        self.symbols_check.setChecked(True)
        self.numbers_check = QCheckBox("Numbers")
        self.numbers_check.setChecked(True)
        self.gen_btn = QPushButton("Generate")
        self.gen_btn.clicked.connect(self.generate)

        gen_layout.addWidget(QLabel("Length:"))
        gen_layout.addWidget(self.length_input)
        gen_layout.addWidget(self.symbols_check)
        gen_layout.addWidget(self.numbers_check)
        gen_layout.addStretch()
        gen_layout.addWidget(self.gen_btn)

        self.save_btn = QPushButton("Save Entry")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #9580ff;
            }}
        """)
        self.save_btn.clicked.connect(self.save)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.save_btn)

        layout.addWidget(QLabel("SITE"))
        layout.addWidget(self.site_input)
        layout.addWidget(QLabel("USERNAME"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("PASSWORD"))
        layout.addWidget(self.password_input)
        layout.addLayout(gen_layout)
        layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def populate_fields(self):
        id_, iv_site, enc_site, iv_user, enc_user, iv_pass, enc_pass = self.entry
        try:
            self.site_input.setText(decrypt_password(iv_site, enc_site, self.key))
            self.username_input.setText(decrypt_password(iv_user, enc_user, self.key))
            self.password_input.setText(decrypt_password(iv_pass, enc_pass, self.key))
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        except Exception:
            self.site_input.setPlaceholderText("Could not decrypt")

    def generate(self):
        password = generate_password(
            length=int(self.length_input.text() or 20),
            use_symbols=self.symbols_check.isChecked(),
            use_numbers=self.numbers_check.isChecked()
        )
        self.password_input.setText(password)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)

    def save(self):
        site = self.site_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not site or not username or not password:
            QMessageBox.warning(self, "Error", "All fields are required")
            return

        if self.entry:
            delete_entry(self.entry[0])

        iv_site, enc_site = encrypt_password(site, self.key)
        iv_user, enc_user = encrypt_password(username, self.key)
        iv_pass, enc_pass = encrypt_password(password, self.key)

        save_entry(self.vault_id, iv_site, enc_site, iv_user, enc_user, iv_pass, enc_pass)
        self.close()
