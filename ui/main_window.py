from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPalette
import pyperclip
from Encryption.vault import decrypt_password
from db.database import get_entries, delete_entry
from ui.add_entry import AddEntryDialog

DARK = {
    "bg": "#1e1e2e",
    "surface": "#2a2a3d",
    "accent": "#7c6af7",
    "text": "#cdd6f4",
    "subtext": "#a6adc8",
    "red": "#f38ba8",
    "green": "#a6e3a1",
}

class MainWindow(QWidget):
    def __init__(self, key: bytes):
        super().__init__()
        self.key = key
        self.setWindowTitle("Secure Password Manager")
        self.setMinimumSize(900, 600)
        self.show_passwords = False
        self.apply_theme()
        self.init_ui()
        self.load_entries()

    def apply_theme(self):
        self.setStyleSheet(f"""
            QWidget {{
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
                border: 1px solid {DARK['accent']};
            }}
            QTableWidget {{
                background-color: {DARK['surface']};
                border: none;
                border-radius: 8px;
                gridline-color: #333355;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #333355;
            }}
            QTableWidget::item:selected {{
                background-color: {DARK['accent']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {DARK['bg']};
                color: {DARK['subtext']};
                padding: 8px;
                border: none;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 11px;
            }}
            QScrollBar:vertical {{
                background: {DARK['bg']};
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: #444466;
                border-radius: 4px;
            }}
        """)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search by site...")
        self.search_input.textChanged.connect(self.filter_entries)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.add_btn = QPushButton("+ Add Entry")
        self.edit_btn = QPushButton("✏ Edit Entry")
        self.copy_btn = QPushButton("⎘ Copy Password")
        self.delete_btn = QPushButton("🗑 Delete Entry")
        self.toggle_btn = QPushButton("👁 Show Passwords")
        self.lock_btn = QPushButton("🔒 Lock Vault")

        self.delete_btn.setStyleSheet(f"color: {DARK['red']};")
        self.lock_btn.setStyleSheet(f"color: {DARK['red']};")

        self.add_btn.clicked.connect(self.open_add_entry)
        self.edit_btn.clicked.connect(self.open_edit_entry)
        self.copy_btn.clicked.connect(self.copy_password)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.toggle_btn.clicked.connect(self.toggle_passwords)
        self.lock_btn.clicked.connect(self.lock_vault)

        for btn in [self.add_btn, self.edit_btn, self.copy_btn,
                    self.delete_btn, self.toggle_btn, self.lock_btn]:
            btn_layout.addWidget(btn)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Site", "Username", "Password"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.search_input)
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

            for col in range(3):
                self.table.item(row, col).setForeground(QColor(DARK['text']))

        self.table.setRowHeight(row, 40) if entries else None

    def filter_entries(self, text):
        filtered = [e for e in self.entries if text.lower() in e[1].lower()]
        self.display_entries(filtered)

    def toggle_passwords(self):
        self.show_passwords = not self.show_passwords
        self.toggle_btn.setText("🙈 Hide Passwords" if self.show_passwords else "👁 Show Passwords")
        self.display_entries(self.entries)

    def copy_password(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Error", "Select an entry first")
            return
        entry = self.entries[row]
        iv, ciphertext = entry[3], entry[4]
        try:
            password = decrypt_password(iv, ciphertext, self.key)
            pyperclip.copy(password)
            QMessageBox.information(self, "Copied", "Password copied. Clipboard clears in 30 seconds.")
            QTimer.singleShot(30000, lambda: pyperclip.copy(""))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Decryption failed: {e}")

    def delete_selected(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Error", "Select an entry first")
            return
        confirm = QMessageBox.question(self, "Confirm", "Delete this entry?")
        if confirm == QMessageBox.StandardButton.Yes:
            entry_id = self.entries[row][0]
            delete_entry(entry_id)
            self.load_entries()

    def open_add_entry(self):
        dialog = AddEntryDialog(self.key, self)
        dialog.exec()
        self.load_entries()

    def open_edit_entry(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Error", "Select an entry first")
            return
        entry = self.entries[row]
        dialog = AddEntryDialog(self.key, self, entry=entry)
        dialog.exec()
        self.load_entries()

    def lock_vault(self):
        from server.local_server import clear_session_key
        clear_session_key()
        self.key = None
        self.close()