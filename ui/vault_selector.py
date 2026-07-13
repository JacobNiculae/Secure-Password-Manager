import hashlib
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QLineEdit, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QScreen
from PyQt6.QtWidgets import QApplication
from Encryption.vault import encrypt, decrypt
from Encryption.keygen import derive_key, generate_salt
from db.database import (
    create_vault, get_vaults, delete_vault, get_entry_count,
    has_legacy_entries, assign_legacy_entries,
    get_master_salt, get_master_hash, get_vault_auth
)

DARK = {
    "bg": "#1e1e2e",
    "surface": "#2a2a3d",
    "accent": "#7c6af7",
    "text": "#cdd6f4",
    "subtext": "#a6adc8",
    "red": "#f38ba8",
    "card": "#252538",
}

COLS = 3
MAX_VAULT_ATTEMPTS = 5


class VaultCard(QFrame):
    def __init__(self, vault_id: int, name: str, entry_count: int, on_open, on_delete):
        super().__init__()
        self.vault_id = vault_id
        self.on_open = on_open
        self.on_delete = on_delete
        self.setFixedSize(210, 155)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            VaultCard {{
                background-color: {DARK['card']};
                border: 1px solid #333355;
                border-radius: 12px;
            }}
            VaultCard:hover {{
                border: 1px solid {DARK['accent']};
                background-color: #2d2d45;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        icon = QLabel("🗄")
        icon.setStyleSheet("font-size: 30px; background: transparent; border: none;")

        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {DARK['subtext']};
                font-size: 12px;
                border-radius: 4px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {DARK['red']};
                color: #1e1e2e;
            }}
        """)
        delete_btn.clicked.connect(lambda: on_delete(vault_id, name))

        top_row.addWidget(icon)
        top_row.addStretch()
        top_row.addWidget(delete_btn)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            color: {DARK['text']};
            font-size: 15px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        name_label.setMaximumWidth(182)
        name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        count_label = QLabel(f"{entry_count} {'entry' if entry_count == 1 else 'entries'}")
        count_label.setStyleSheet(f"color: {DARK['subtext']}; font-size: 12px; background: transparent; border: none;")

        layout.addLayout(top_row)
        layout.addSpacing(2)
        layout.addWidget(name_label)
        layout.addWidget(count_label)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_open(self.vault_id)

    def enterEvent(self, event):
        self.setStyleSheet(f"""
            VaultCard {{
                background-color: #2d2d45;
                border: 1px solid {DARK['accent']};
                border-radius: 12px;
            }}
        """)

    def leaveEvent(self, event):
        self.setStyleSheet(f"""
            VaultCard {{
                background-color: {DARK['card']};
                border: 1px solid #333355;
                border-radius: 12px;
            }}
        """)


class VaultSelectorWindow(QWidget):
    def __init__(self, key: bytes, on_open_vault, on_lock):
        super().__init__()
        self.key = key
        self.on_open_vault = on_open_vault
        self.on_lock = on_lock
        self._drag_pos = None
        self.setWindowTitle("Secure Password Manager")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(860, 560)
        self._migrate_legacy()
        self.apply_theme()
        self.init_ui()
        self.load_vaults()
        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(900, 580)
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _migrate_legacy(self):
        if has_legacy_entries() and not get_vaults():
            iv, enc = encrypt(["General"], self.key)[0]
            master_salt = get_master_salt()
            master_hash = get_master_hash()
            vault_id = create_vault(iv, enc, master_salt, master_hash)
            assign_legacy_entries(vault_id)

    def apply_theme(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {DARK['bg']};
                color: {DARK['text']};
                font-family: 'Segoe UI';
                font-size: 13px;
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
            QScrollBar:vertical {{
                background: {DARK['bg']};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: #444466;
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar:horizontal {{ height: 0px; }}
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(44)
        title_bar.setStyleSheet(f"background-color: {DARK['surface']}; border-bottom: 1px solid #2e2e45;")
        tbl = QHBoxLayout(title_bar)
        tbl.setContentsMargins(18, 0, 10, 0)

        title_label = QLabel("🔐  Secure Password Manager")
        title_label.setStyleSheet(f"color: {DARK['text']}; font-weight: bold; font-size: 13px;")

        minimize_btn = QPushButton("—")
        minimize_btn.setFixedSize(34, 34)
        minimize_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {DARK['subtext']}; font-size: 14px;
            }}
            QPushButton:hover {{ background: #444466; border-radius: 6px; color: white; }}
        """)
        minimize_btn.clicked.connect(self.showMinimized)

        lock_btn = QPushButton("🔒  Lock")
        lock_btn.setFixedSize(80, 32)
        lock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2e1e28;
                border: 1px solid {DARK['red']};
                border-radius: 6px;
                color: {DARK['red']};
                font-size: 12px;
                font-weight: bold;
                padding: 0px 8px;
            }}
            QPushButton:hover {{
                background-color: {DARK['red']};
                color: #1e1e2e;
            }}
        """)
        lock_btn.clicked.connect(self._do_lock)

        tbl.addWidget(title_label)
        tbl.addStretch()
        tbl.addWidget(minimize_btn)
        tbl.addWidget(lock_btn)

        title_bar.mousePressEvent = self._title_press
        title_bar.mouseMoveEvent = self._title_move

        # Content
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(32, 28, 32, 28)
        cl.setSpacing(22)

        # Header row
        header_row = QHBoxLayout()
        vaults_label = QLabel("My Vaults")
        vaults_label.setStyleSheet(f"color: {DARK['text']}; font-size: 22px; font-weight: bold;")

        add_btn = QPushButton("  + Add Vault")
        add_btn.setFixedHeight(38)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0px 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #9580ff; border: none; }}
        """)
        add_btn.clicked.connect(self.add_vault)

        header_row.addWidget(vaults_label)
        header_row.addStretch()
        header_row.addWidget(add_btn)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.cards_widget = QWidget()
        self.cards_widget.setStyleSheet("background: transparent;")
        self.cards_layout = QGridLayout(self.cards_widget)
        self.cards_layout.setSpacing(18)
        self.cards_layout.setContentsMargins(2, 2, 2, 2)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self.cards_widget)

        self.empty_label = QLabel("No vaults yet.\nClick  '+ Add Vault'  to create your first vault.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"color: {DARK['subtext']}; font-size: 15px; line-height: 1.6;")
        self.empty_label.hide()

        cl.addLayout(header_row)
        cl.addWidget(scroll, 1)
        cl.addWidget(self.empty_label, 1)

        layout.addWidget(title_bar)
        layout.addWidget(content, 1)

    def _title_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _title_move(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def load_vaults(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        vaults_raw = get_vaults()

        if not vaults_raw:
            self.cards_widget.hide()
            self.empty_label.show()
            return

        self.cards_widget.show()
        self.empty_label.hide()

        for i, (vault_id, iv_name, enc_name) in enumerate(vaults_raw):
            try:
                name = decrypt(iv_name, enc_name, self.key)
            except Exception:
                name = "⚠ Corrupted"
            count = get_entry_count(vault_id)
            card = VaultCard(vault_id, name, count, self._open_vault, self._delete_vault)
            self.cards_layout.addWidget(card, i // COLS, i % COLS)

    def _open_vault(self, vault_id: int):
        vault_salt, vault_hash = get_vault_auth(vault_id)
        if vault_salt is None or vault_hash is None:
            return
        name = self._get_vault_name(vault_id)
        dlg = _VaultUnlockDialog(self, name, vault_salt, vault_hash)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.vault_key is not None:
            self.on_open_vault(dlg.vault_key, vault_id, name)

    def _get_vault_name(self, vault_id: int) -> str:
        for v_id, iv_name, enc_name in get_vaults():
            if v_id == vault_id:
                try:
                    return decrypt(iv_name, enc_name, self.key)
                except Exception:
                    return "Vault"
        return "Vault"

    def _delete_vault(self, vault_id: int, name: str):
        count = get_entry_count(vault_id)
        msg = f'Delete vault "{name}"?\n\nThis will permanently delete {count} {"entry" if count == 1 else "entries"}.'
        dlg = _ConfirmDeleteDialog(self, msg)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            delete_vault(vault_id)
            self.load_vaults()

    def add_vault(self):
        dlg = _AddVaultDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.get_name()
            password = dlg.get_password()
            if name and password:
                vault_salt = generate_salt()
                vault_key = derive_key(password, vault_salt)
                vault_hash = hashlib.sha256(vault_key).digest()
                iv, enc = encrypt([name], self.key)[0]
                create_vault(iv, enc, vault_salt, vault_hash)
                self.load_vaults()

    def _do_lock(self):
        self.on_lock()
        # on_lock() (lock_vault in main.py) already closes this window


# ──────────────────────────────────────────
#  Vault unlock dialog
# ──────────────────────────────────────────
class _VaultUnlockDialog(QDialog):
    def __init__(self, parent, vault_name: str, vault_salt: bytes, vault_hash: bytes):
        super().__init__(parent)
        self.vault_salt = vault_salt
        self.vault_hash = vault_hash
        self.vault_key = None
        self.attempts = 0
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(400, 290)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DARK['bg']};
                border: 1px solid #444466;
                border-radius: 14px;
            }}
            QWidget {{ background-color: {DARK['bg']}; font-family: 'Segoe UI'; color: {DARK['text']}; }}
            QLineEdit {{
                background-color: {DARK['surface']};
                border: 1px solid #444466;
                border-radius: 8px;
                padding: 10px 12px;
                color: {DARK['text']};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {DARK['accent']}; }}
            QPushButton {{
                border-radius: 8px;
                padding: 9px 22px;
                font-size: 13px;
                font-weight: bold;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(0)

        icon = QLabel("🗄")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 38px; background: transparent;")

        title = QLabel(f'Unlock  "{vault_name}"')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {DARK['text']}; font-size: 16px; font-weight: bold; margin-top: 6px;")

        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet(f"color: {DARK['red']}; font-size: 12px; margin-top: 4px;")
        self.error_label.setFixedHeight(20)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Vault password...")
        self.password_input.returnPressed.connect(self._attempt)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK['surface']};
                color: {DARK['text']};
                border: 1px solid #444466;
            }}
            QPushButton:hover {{ background-color: #444466; border: 1px solid #444466; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        self.unlock_btn = QPushButton("Unlock")
        self.unlock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK['accent']};
                color: white;
                border: none;
            }}
            QPushButton:hover {{ background-color: #9580ff; border: none; }}
        """)
        self.unlock_btn.clicked.connect(self._attempt)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.unlock_btn)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(self.error_label)
        layout.addSpacing(12)
        layout.addWidget(self.password_input)
        layout.addSpacing(18)
        layout.addLayout(btn_row)

    def _attempt(self):
        password = self.password_input.text()
        if not password:
            return

        # Argon2id key derivation + AES-GCM verification
        derived = derive_key(password, self.vault_salt)
        verification = hashlib.sha256(derived).digest()

        if verification == self.vault_hash:
            self.vault_key = derived
            self.accept()
            return

        self.attempts += 1
        remaining = MAX_VAULT_ATTEMPTS - self.attempts
        self.password_input.clear()

        if self.attempts >= MAX_VAULT_ATTEMPTS:
            self.error_label.setText("Too many failed attempts.")
            self.unlock_btn.setEnabled(False)
            self.password_input.setEnabled(False)
        else:
            self.error_label.setText(f"Wrong password — {remaining} attempt{'s' if remaining != 1 else ''} left.")


# ──────────────────────────────────────────
#  Add vault dialog
# ──────────────────────────────────────────
class _AddVaultDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(400, 390)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DARK['bg']};
                border: 1px solid #444466;
                border-radius: 14px;
            }}
            QWidget {{ background-color: {DARK['bg']}; font-family: 'Segoe UI'; color: {DARK['text']}; }}
            QLineEdit {{
                background-color: {DARK['surface']};
                border: 1px solid #444466;
                border-radius: 8px;
                padding: 10px 12px;
                color: {DARK['text']};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {DARK['accent']}; }}
            QPushButton {{
                border-radius: 8px;
                padding: 9px 22px;
                font-size: 13px;
                font-weight: bold;
            }}
            QLabel#field_label {{
                color: {DARK['subtext']};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(8)

        title = QLabel("New Vault")
        title.setStyleSheet(f"color: {DARK['text']}; font-size: 18px; font-weight: bold; margin-bottom: 4px;")

        name_lbl = QLabel("VAULT NAME")
        name_lbl.setObjectName("field_label")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Work, Personal, Banking...")

        pw_lbl = QLabel("VAULT PASSWORD")
        pw_lbl.setObjectName("field_label")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Choose a strong password")

        conf_lbl = QLabel("CONFIRM PASSWORD")
        conf_lbl.setObjectName("field_label")
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Repeat the password")
        self.confirm_input.returnPressed.connect(self._accept)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {DARK['red']}; font-size: 12px;")
        self.error_label.setFixedHeight(18)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK['surface']};
                color: {DARK['text']};
                border: 1px solid #444466;
            }}
            QPushButton:hover {{ background-color: #444466; border: 1px solid #444466; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        create_btn = QPushButton("Create Vault")
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK['accent']};
                color: white;
                border: none;
            }}
            QPushButton:hover {{ background-color: #9580ff; border: none; }}
        """)
        create_btn.clicked.connect(self._accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(create_btn)

        layout.addWidget(title)
        layout.addSpacing(6)
        layout.addWidget(name_lbl)
        layout.addWidget(self.name_input)
        layout.addSpacing(4)
        layout.addWidget(pw_lbl)
        layout.addWidget(self.password_input)
        layout.addSpacing(4)
        layout.addWidget(conf_lbl)
        layout.addWidget(self.confirm_input)
        layout.addWidget(self.error_label)
        layout.addStretch()
        layout.addLayout(btn_row)

    def _accept(self):
        name = self.name_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not name:
            self.error_label.setText("Vault name is required.")
            return
        if not password:
            self.error_label.setText("Password is required.")
            return
        if len(password) < 8:
            self.error_label.setText("Password must be at least 8 characters.")
            return
        if password != confirm:
            self.error_label.setText("Passwords do not match.")
            self.confirm_input.clear()
            return

        self.accept()

    def get_name(self) -> str:
        return self.name_input.text().strip()

    def get_password(self) -> str:
        return self.password_input.text()


# ──────────────────────────────────────────
#  Confirm delete dialog
# ──────────────────────────────────────────
class _ConfirmDeleteDialog(QDialog):
    def __init__(self, parent, message: str):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(400, 210)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DARK['bg']};
                border: 1px solid {DARK['red']};
                border-radius: 14px;
            }}
            QWidget {{ background-color: {DARK['bg']}; font-family: 'Segoe UI'; color: {DARK['text']}; }}
            QPushButton {{
                border-radius: 8px;
                padding: 9px 22px;
                font-size: 13px;
                font-weight: bold;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        warning = QLabel("⚠  WARNING")
        warning.setStyleSheet(f"color: {DARK['red']}; font-size: 13px; font-weight: bold;")
        warning.setAlignment(Qt.AlignmentFlag.AlignCenter)

        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet("font-size: 13px;")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK['surface']};
                color: {DARK['text']};
                border: 1px solid #444466;
            }}
            QPushButton:hover {{ background-color: #444466; border: 1px solid #444466; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK['red']};
                color: #1e1e2e;
                border: none;
            }}
            QPushButton:hover {{ background-color: #ff9eb5; border: none; }}
        """)
        delete_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(delete_btn)

        layout.addWidget(warning)
        layout.addWidget(msg)
        layout.addStretch()
        layout.addLayout(btn_row)
