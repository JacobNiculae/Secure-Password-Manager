from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
import pyperclip
from Encryption.vault import decrypt_password
from db.database import get_entries, delete_entry
from ui.add_entry import AddEntryDialog

class MainWindow(QWidget):
    def __init__(self, key: bytes):
        super().__init__()
        self.key = key
        self.setWindowTitle("Secure Password Manager")
        self.setMinimumSize(700, 500)
        self.show_passwords = False
        self.init_ui()
        self.load_entries()

    def init_ui(self):
        layout = QVBoxLayout()

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by site...")
        self.search_input.textChanged.connect(self.filter_entries)
        search_layout.addWidget(self.search_input)

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Entry")
        self.add_btn.clicked.connect(self.open_add_entry)
        self.copy_btn = QPushButton("Copy Password")
        self.copy_btn.clicked.connect(self.copy_password)
        self.delete_btn = QPushButton("Delete Entry")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.toggle_btn = QPushButton("Show Passwords")
        self.toggle_btn.clicked.connect(self.toggle_passwords)
        self.lock_btn = QPushButton("Lock Vault")
        self.lock_btn.clicked.connect(self.lock_vault)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.toggle_btn)
        btn_layout.addWidget(self.lock_btn)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Site", "Username", "Password"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addLayout(search_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_entries(self):
        self.entries = get_entries()
        self.display_entries(self.entries)

    def display_entries(self, entries):
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            id_, site, username, iv, ciphertext = entry
            try:
                password = decrypt_password(iv, ciphertext, self.key)
            except Exception:
                password = "[decryption failed]"
            self.table.setItem(row, 0, QTableWidgetItem(site))
            self.table.setItem(row, 1, QTableWidgetItem(username))
            if self.show_passwords:
                self.table.setItem(row, 2, QTableWidgetItem(password))
            else:
                self.table.setItem(row, 2, QTableWidgetItem("••••••••"))

    def filter_entries(self, text):
        filtered = [e for e in self.entries if text.lower() in e[1].lower()]
        self.display_entries(filtered)

    def toggle_passwords(self):
        self.show_passwords = not self.show_passwords
        self.toggle_btn.setText("Hide Passwords" if self.show_passwords else "Show Passwords")
        self.display_entries(self.entries)

    def copy_password(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Error", "Select an entry first")
            return
        entry = self.entries[row]
        print(f"Entry: {entry}")
        print(f"IV type: {type(entry[3])}, length: {len(entry[3])}")
        print(f"Ciphertext type: {type(entry[4])}, length: {len(entry[4])}")
        print(f"Key type: {type(self.key)}, length: {len(self.key)}")
        iv, ciphertext = entry[3], entry[4]
        try:
            password = decrypt_password(iv, ciphertext, self.key)
            pyperclip.copy(password)
            QMessageBox.information(self, "Copied", "Password copied.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Decryption failed: {e}")
    
    def delete_selected(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Error", "Select an entry first")
            return
        entry_id = self.entries[row][0]
        delete_entry(entry_id)
        self.load_entries()

    def open_add_entry(self):
        dialog = AddEntryDialog(self.key, self)
        dialog.exec()
        self.load_entries()

    def lock_vault(self):
        from server.local_server import clear_session_key
        clear_session_key()
        self.key = None
        self.close()