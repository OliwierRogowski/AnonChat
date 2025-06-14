import sys
import os
from PyQt6.QtWidgets import QApplication
from login import LoginWindow
from adminPanel import AdminWindow
from chat import ChatWindow
from db import connect_db
from config import load_encrypted_config
from keyring_utils import load_password
from chat_logic import ChatHandler
from userLoggedData import User

class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.loginWindow = LoginWindow(self.login)
        self.mainWindow = None
        self.conn = None
        self.chat_handler = None

    def login(self, userType, userName, password):
        self.loginWindow.close()

        private_key_password = password.encode('utf-8')

        # Połączenie do bazy i inicjalizacja ChatHandlera
        config = load_encrypted_config()
        self.conn = connect_db(
            config["dbname"],
            'adminanonchat',
            load_password('adminanonchat'),  # Hasło do bazy
            config["host"],
            config["port"]
        )
        # Poprawna obsługa ścieżki do klucza prywatnego
        private_key_path = os.path.expanduser("~/.anonChat/private_key.pem")
        self.chat_handler = ChatHandler(
            conn=self.conn,
            private_key_file=private_key_path,
            private_key_password=private_key_password
        )
        cur = self.conn.cursor()
        cur.execute("SELECT id, public_key FROM users WHERE username = %s", (userName,))
        row = cur.fetchone()
        if row is None:
            print(f"Użytkownik '{userName}' nie istnieje w bazie danych.")
            cur.close()
            return

        user_id = row['id']
        # Ostrzeżenie, jeśli użytkownik nie ma klucza publicznego
        if not row['public_key']:
            print(f"Użytkownik '{userName}' nie ma ustawionego klucza publicznego! Szyfrowanie wiadomości nie będzie działać.")
        cur.close()

        session = self.create_session(userName, "admin" if userType == "admin" else "user", user_id)
        if userType == "admin":
            self.mainWindow = AdminWindow(session)
        else:
            self.mainWindow = ChatWindow(session, self.conn, self.chat_handler, private_key_password)

        self.mainWindow.resize(1000, 1000)
        self.mainWindow.show()

    def create_session(self, username, isAdmin, user_id):
        return User(username=username, isAdmin=isAdmin, user_id=user_id)

    def run(self):
        self.loginWindow.show()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = AppController()
    app.run()
