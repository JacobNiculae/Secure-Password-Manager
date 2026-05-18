import sys
import os
import threading
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from ui.vault_selector import VaultSelectorWindow
from server.local_server import run_server, clear_session_key, set_session_vault, clear_session_vault
from db.database import init_db

main_window = None
vault_selector = None
login_window = None
tray_icon = None
app = None

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def start_server():
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

def show_vault_selector(key: bytes):
    global vault_selector
    if vault_selector is not None:
        # Reuse the existing window — just refresh and show (no flicker)
        vault_selector.load_vaults()
        vault_selector.show()
        vault_selector.raise_()
        vault_selector.activateWindow()
        return
    vault_selector = VaultSelectorWindow(key, on_open_vault=open_vault, on_lock=full_lock)
    vault_selector.show()

def open_vault(key: bytes, vault_id: int, vault_name: str):
    global main_window, vault_selector
    set_session_vault(vault_id)
    # Show main window first, then hide selector — prevents black-flash between windows
    main_window = MainWindow(key, vault_id, vault_name, on_back=lambda: _back_to_selector(key))
    main_window.show()
    if vault_selector:
        vault_selector.hide()

def _back_to_selector(key: bytes):
    global main_window
    clear_session_vault()
    # Show vault selector first, then close main window — prevents black-flash
    show_vault_selector(key)
    old = main_window
    main_window = None
    if old:
        old.close()

def show_login():
    global login_window
    if login_window and login_window.isVisible():
        return
    login_window = LoginWindow(on_success=on_login_success)
    login_window.show()

def on_login_success(key: bytes):
    global vault_selector
    # Always create a fresh vault selector after login
    vault_selector = None
    update_tray(key)
    show_vault_selector(key)

def full_lock():
    """Lock everything and return to master-password login screen."""
    global main_window, vault_selector
    clear_session_key()
    if main_window:
        main_window.close()
        main_window = None
    if vault_selector:
        vault_selector.close()
        vault_selector = None
    update_tray(None)
    show_login()

def update_tray(key):
    global tray_icon
    menu = QMenu()

    if key:
        open_action = menu.addAction("Open Vaults")
        open_action.triggered.connect(lambda: show_vault_selector(key))
        lock_action = menu.addAction("Lock")
        lock_action.triggered.connect(full_lock)
    else:
        unlock_action = menu.addAction("Unlock")
        unlock_action.triggered.connect(show_login)

    menu.addSeparator()
    quit_action = menu.addAction("Quit")
    quit_action.triggered.connect(quit_app)

    tray_icon.setContextMenu(menu)
    status = "🔓 Unlocked" if key else "🔒 Locked"
    tray_icon.setToolTip(f"Secure Password Manager — {status}")

def quit_app():
    clear_session_key()
    QApplication.quit()

def main():
    global app, tray_icon, login_window

    init_db()
    start_server()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)

    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(QIcon(resource_path("icon.ico")))
    tray_icon.setVisible(True)
    update_tray(None)

    tray_icon.activated.connect(lambda reason: show_login()
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)

    login_window = LoginWindow(on_success=on_login_success)
    login_window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
