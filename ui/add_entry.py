from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
QLineEdit, QPushButton, QCheckBox, QSpinBox, QMessageBox)
from Encryption.vault import encrypt_password
from db.database import save_entry
from utils.password_gen import generate_password

class AddEntryDialog(QDialog):
    def __init__(self, key: bytes, parent=None):
        super().__init__(parent)
        self.key = key
        self.setWindowTitle("Add New Entry")
        self.setFixedSize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Site input
        self.site_input = QLineEdit()
        self.site_input.setPlaceholderText("Site (e.g. google.com)")

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username or email")

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Password generator options
        gen_layout = QHBoxLayout()
        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 64)
        self.length_spin.setValue(20)
        self.symbols_check = QCheckBox("Symbols")
        self.symbols_check.setChecked(True)
        self.numbers_check = QCheckBox("Numbers")
        self.numbers_check.setChecked(True)
        self.gen_btn = QPushButton("Generate Password")
        self.gen_btn.clicked.connect(self.generate)

        gen_layout.addWidget(QLabel("Length:"))
        gen_layout.addWidget(self.length_spin)
        gen_layout.addWidget(self.symbols_check)
        gen_layout.addWidget(self.numbers_check)

        # Save button
        self.save_btn = QPushButton("Save Entry")
        self.save_btn.clicked.connect(self.save)

        layout.addWidget(QLabel("Site"))
        layout.addWidget(self.site_input)
        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password"))
        layout.addWidget(self.password_input)
        layout.addLayout(gen_layout)
        layout.addWidget(self.gen_btn)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

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

        iv, ciphertext = encrypt_password(password, self.key)
        save_entry(site, username, iv, ciphertext)
        QMessageBox.information(self, "Saved", "Entry saved successfully")
        self.close()