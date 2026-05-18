from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QLabel)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
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
    def __init__(self, key: bytes, vault_id: int, vault_name: str, on_back=None):
        super().__init__()
        self.key = key
        self.vault_id = vault_id
        self.vault_name = vault_name
        self.on_back = on_back
        self.setWindowTitle("Secure Password Manager")
        self.setMinimumSize(900, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.show_passwords = False
        self._drag_pos = None
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Custom title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet(f"background-color: {DARK['surface']}; border-bottom: 1px solid #333355;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 0, 8, 0)

        title_label = QLabel(f"🔐 {self.vault_name}")
        title_label.setStyleSheet(f"color: {DARK['text']}; font-weight: bold; font-size: 13px;")

        minimize_btn = QPushButton("—")
        minimize_btn.setFixedSize(32, 32)
        minimize_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {DARK['subtext']};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: #444466;
                border-radius: 4px;
                color: white;
            }}
        """)
        minimize_btn.clicked.connect(self.showMinimized)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(minimize_btn)

        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move

        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 20)
        content_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search by site...")
        self.search_input.textChanged.connect(self.filter_entries)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.back_btn = QPushButton("← Vaults")
        self.add_btn = QPushButton("+ Add Entry")
        self.edit_btn = QPushButton("✏ Edit Entry")
        self.copy_btn = QPushButton("⎘ Copy Password")
        self.delete_btn = QPushButton("🗑 Delete Entry")
        self.toggle_btn = QPushButton("👁 Show Passwords")
        self.lock_btn = QPushButton("🔒 Lock All")

        self.delete_btn.setStyleSheet(f"color: {DARK['red']};")
        self.lock_btn.setStyleSheet(f"color: {DARK['red']};")

        self.back_btn.clicked.connect(self.go_back)
        self.add_btn.clicked.connect(self.open_add_entry)
        self.edit_btn.clicked.connect(self.open_edit_entry)
        self.copy_btn.clicked.connect(self.copy_password)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.toggle_btn.clicked.connect(self.toggle_passwords)
        self.lock_btn.clicked.connect(self.lock_all)

        for btn in [self.back_btn, self.add_btn, self.edit_btn, self.copy_btn,
                    self.delete_btn, self.toggle_btn, self.lock_btn]:
            btn_layout.addWidget(btn)

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

        content_layout.addWidget(self.search_input)
        content_layout.addLayout(btn_layout)
        content_layout.addWidget(self.table)

        layout.addWidget(title_bar)
        layout.addWidget(content)
        self.setLayout(layout)

    def title_bar_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def title_bar_mouse_move(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def load_entries(self):
        self.entries = get_entries(self.vault_id)
        self.display_entries(self.entries)

    def display_entries(self, entries):
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            _, iv_site, enc_site, iv_user, enc_user, iv_pass, enc_pass = entry
            try:
                site = decrypt_password(iv_site, enc_site, self.key)
                username = decrypt_password(iv_user, enc_user, self.key)
                password = decrypt_password(iv_pass, enc_pass, self.key)
            except Exception:
                site = "[error]"
                username = "[error]"
                password = "[error]"

            self.table.setItem(row, 0, QTableWidgetItem(site))
            self.table.setItem(row, 1, QTableWidgetItem(username))
            if self.show_passwords:
                self.table.setItem(row, 2, QTableWidgetItem(password))
            else:
                self.table.setItem(row, 2, QTableWidgetItem("••••••••"))

            for col in range(3):
                self.table.item(row, col).setForeground(QColor(DARK['text']))

    def filter_entries(self, text):
        if not text:
            self.display_entries(self.entries)
            return
        filtered = []
        for entry in self.entries:
            try:
                site = decrypt_password(entry[1], entry[2], self.key)
                if text.lower() in site.lower():
                    filtered.append(entry)
            except Exception:
                pass
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
        id_, iv_site, enc_site, iv_user, enc_user, iv_pass, enc_pass = entry
        try:
            password = decrypt_password(iv_pass, enc_pass, self.key)
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
        dialog = AddEntryDialog(self.key, self.vault_id, self)
        dialog.raise_()
        dialog.activateWindow()
        dialog.exec()
        self.load_entries()

    def open_edit_entry(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Error", "Select an entry first")
            return
        entry = self.entries[row]
        dialog = AddEntryDialog(self.key, self.vault_id, self, entry=entry)
        dialog.raise_()
        dialog.activateWindow()
        dialog.exec()
        self.load_entries()

    def go_back(self):
        if self.on_back:
            self.on_back()
        # on_back (_back_to_selector) shows vault selector then closes this window

    def lock_all(self):
        from main import full_lock
        full_lock()
        # full_lock() closes this window
