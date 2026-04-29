import sys
import threading
from PyQt6.QtWidgets import QApplication
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from server.local_server import run_server
from db.database import init_db

main_window = None

def start_server():
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

def main():
    global main_window
    init_db()
    start_server()

    app = QApplication(sys.argv)

    def on_login_success(key: bytes):
        global main_window
        main_window = MainWindow(key)
        main_window.show()

    login = LoginWindow(on_success=on_login_success)
    login.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()