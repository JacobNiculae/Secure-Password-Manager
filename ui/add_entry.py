from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
QLineEdit, QPushButton, QCheckBox, QSpinBox, QMessageBox)
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
    def __init__(self, key: bytes, parent=None, entry=None):
        super().__init__(parent)
        self.key = key
        self.entry = entry
        self.setWindowTitle("Edit Entry" if entry else "Add New Entry")
        self.setFixedSize(420, 320)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.apply_theme()
        self.init_ui()
        if entry:
            self.populate_fields()

    def apply_theme(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DARK['bg']};
                color: {DARK['text']};
                font-family: 'Segoe UI';
                font-size: 13px;
            }}
            QLineEdit {{
                background-color: {DARK['surface']};
                border: 1px solid #444466;
                border-radius: 6px;
                padding: 6px 10px;
                color: {DARK['text']};
            }}
            QPushButton {{
                background-color: {DARK['surface']};
                color: {DARK['text']};
                border: 1px solid #444466;
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: {DARK['accent']};
                color: white;
            }}
            QLabel {{
                color: {DARK['subtext']};
                font-size: 11px;
                font-weight: bold;
            }}
            QCheckBox {{
                color: {DARK['text']};
            }}
            QSpinBox {{
                background-color: {DARK['surface']};
                color: {DARK['text']};
                border: 1px solid #444466;
                border-radius: 6px;
                padding: 4px;
            }}
        """)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(20, 20, 20, 20)

        self.site_input = QLineEdit()
        self.site_input.setPlaceholderText("e.g. google.com")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username or email")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        gen_layout = QHBoxLayout()
        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 64)
        self.length_spin.setValue(20)
        self.symbols_check = QCheckBox("Symbols")
        self.symbols_check.setChecked(True)
        self.numbers_check = QCheckBox("Numbers")
        self.numbers_check.setChecked(True)
        self.gen_btn = QPushButton("Generate")
        self.gen_btn.clicked.connect(self.generate)

        gen_layout.addWidget(QLabel("Length:"))
        gen_layout.addWidget(self.length_spin)
        gen_layout.addWidget(self.symbols_check)
        gen_layout.addWidget(self.numbers_check)
        gen_layout.addWidget(self.gen_btn)

        self.save_btn = QPushButton("Save Entry")
        self.save_btn.clicked.connect(self.save)

        layout.addWidget(QLabel("SITE"))
        layout.addWidget(self.site_input)
        layout.addWidget(QLabel("USERNAME"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("PASSWORD"))
        layout.addWidget(self.password_input)
        layout.addLayout(gen_layout)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

    def populate_fields(self):
        id_, site, username, iv, ciphertext = self.entry
        self.site_input.setText(site)
        self.username_input.setText(username)
        try:
            password = decrypt_password(iv, ciphertext, self.key)
            self.password_input.setText(password)
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        except Exception:
            self.password_input.setPlaceholderText("Could not decrypt")

    def generate(self):
        password = generate_password(
            length=self.length_spin.value(),
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

        iv, ciphertext = encrypt_password(password, self.key)
        save_entry(site, username, iv, ciphertext)
        QMessageBox.information(self, "Saved", "Entry saved successfully")
        self.close()