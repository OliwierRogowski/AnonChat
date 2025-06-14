from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QMessageBox
)
from db import connect_db
from password_hasher import PasswordHasher
from generate_key import GenerateKey
import traceback
import os

class LoginWindow(QWidget):
    def __init__(self, loginCallback):
        super().__init__()
        self.setWindowTitle("AnonChat - Anonymous chat for firms")

        self.loginCallback = loginCallback

        self.label = QLabel("Zaloguj się")
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Hasło")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Zaloguj")
        self.login_button.clicked.connect(self.loginHandler)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.email)
        layout.addWidget(self.password)
        layout.addWidget(self.login_button)
        self.setLayout(layout)

    def loginHandler(self):
        try:
            username = self.email.text()
            password = self.password.text()

            # Połącz z bazą (pamiętaj, zmień parametry na swoje)
            conn = connect_db("anonChatDb", "adminanonchat", "123", "localhost", "5432")
            cur = conn.cursor()

            cur.execute(
                "SELECT password, isadmin FROM users WHERE username = %s",
                (username,)
            )
            result = cur.fetchone()

            if result:
                stored_hashed_password = result['password']
                isAdmin = result['isadmin']

                if PasswordHasher.verify_password(password, stored_hashed_password):
                    # Generuj klucz dla zwykłego użytkownika (opcjonalnie)
                    if not isAdmin:
                        password_bytes = password.encode()
                        gen = GenerateKey()
                        private_key_path = gen.generate_private_key(password_bytes, os.path.expanduser(f"~/.anonChat/keys/{username}.private_key.pem"))
                    else:
                        private_key_path = "/path/to/admin/private_key.pem"  # popraw to na właściwą ścieżkę admina



                    # Przekaż info do kontrolera aplikacji, w tym hasło plaintext
                    self.loginCallback("admin" if isAdmin else "user", username, password)
                    self.close()
                    return
            
            QMessageBox.warning(self, "Błąd logowania", "Nieprawidłowa nazwa użytkownika lub hasło.")
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            QMessageBox.critical(self, "Błąd", f"Coś poszło nie tak:\n{tb}")

