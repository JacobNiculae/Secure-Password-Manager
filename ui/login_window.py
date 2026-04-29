from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from Encryption.keygen import derive_key, generate_salt
from db.database import init_db, save_master_salt, get_master_salt
from server.local_server import set_session_key

class LoginWindow(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.setWindowTitle("Secure Password Manager")
        self.setFixedSize(400, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Enter Master Password")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Master password...")

        self.submit_btn = QPushButton("Unlock Vault")
        self.submit_btn.clicked.connect(self.handle_login)

        layout.addWidget(self.label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.submit_btn)

        self.setLayout(layout)

    def handle_login(self):
        password = self.password_input.text()

        if not password:
            QMessageBox.warning(self, "Error", "Password cannot be empty")
            return

        init_db()
        salt = get_master_salt()

        if salt is None:
            salt = generate_salt()
            save_master_salt(salt)

        key = derive_key(password, salt)
        set_session_key(key)
        self.on_success(key)
        self.close()