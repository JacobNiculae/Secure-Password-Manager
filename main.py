import sys
import os
import threading
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from server.local_server import run_server, clear_session_key
from db.database import init_db

main_window = None
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

def open_vault(key):
    global main_window
    if main_window and main_window.isVisible():
        main_window.raise_()
        main_window.activateWindow()
        return
    main_window = MainWindow(key)
    main_window.show()

def show_login():
    global login_window
    if login_window and login_window.isVisible():
        return
    login_window = LoginWindow(on_success=on_login_success)
    login_window.show()

def on_login_success(key: bytes):
    global tray_icon
    update_tray(key)
    open_vault(key)

def lock_vault():
    global main_window
    clear_session_key()
    if main_window:
        main_window.close()
        main_window = None
    update_tray(None)

def update_tray(key):
    global tray_icon
    menu = QMenu()

    if key:
        open_action = menu.addAction("Open Vault")
        open_action.triggered.connect(lambda: open_vault(key))
        lock_action = menu.addAction("Lock Vault")
        lock_action.triggered.connect(lock_vault)
    else:
        unlock_action = menu.addAction("Unlock Vault")
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