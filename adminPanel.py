import sys
from generate_key import GenerateKey
import bcrypt
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QLabel, QLineEdit, QWidget,
    QApplication, QPushButton, QMessageBox, QTabWidget, QHBoxLayout,
    QListWidget, QStackedWidget, QCheckBox, QFormLayout
)
from keyring_utils import save_password, load_password
from config import save_encrypted_config, load_encrypted_config
from db import connect_db


class AdminWindow(QMainWindow):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle(f"AnonChat - Panel administratora {self.session.username}")

        self.isConnectedToDatabase = False

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.addItems(["Strona główna", "Konfiguracja", "Logi", "Użytkownicy"])
        self.sidebar.currentRowChanged.connect(self.display_view)

        # Stack
        self.stack = QStackedWidget()
        self.init_views()

        main_layout.addWidget(self.sidebar, 1)
        main_layout.addWidget(self.stack, 4)

    def init_views(self):
        # Widok do dodawania użytkownika
        add_user_widget = QWidget()
        form_layout = QFormLayout()

        self.login = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.reap = QLineEdit()
        self.reap.setEchoMode(QLineEdit.EchoMode.Password)
        self.isAdminCheckBox = QCheckBox("Czy administrator?")
        self.comunicatIfAdded = QLabel()

        add_button = QPushButton("Dodaj użytkownika")
        add_button.clicked.connect(self.add_user)

        form_layout.addRow("Login:", self.login)
        form_layout.addRow("Hasło:", self.password)
        form_layout.addRow("Powtórz hasło:", self.reap)
        form_layout.addRow("", self.isAdminCheckBox)
        form_layout.addRow(add_button)
        form_layout.addRow("", self.comunicatIfAdded)

        add_user_widget.setLayout(form_layout)
        self.stack.addWidget(add_user_widget)

        # Placeholdery dla pozostałych zakładek
        self.stack.addWidget(QWidget())  # "Konfiguracja" - przy instalce jako konfigurator config.json
        self.stack.addWidget(QWidget())  # "Logi"
        self.stack.addWidget(QWidget())  # "Użytkownicy"

    def display_view(self, index):
        self.stack.setCurrentIndex(index)

    def add_user(self):
        config = load_encrypted_config()
        try:
            conn = connect_db(config["dbname"], 'adminanonchat', load_password('adminanonchat'),
                              config["host"], config["port"])
        except Exception as e:
            self.comunicatIfAdded.setText(f"❌ Błąd połączenia z bazą: {e}")
            return

        cur = conn.cursor()
        username = self.login.text()
        cur.execute("SELECT username FROM users WHERE username=%s", (username,))
        row = cur.fetchone()

        if row:
            self.comunicatIfAdded.setText("❌ Nie dodano użytkownika. Login już istnieje.")
            conn.close()
            return

        password = self.password.text()
        retyped = self.reap.text()
        if password != retyped:
            self.comunicatIfAdded.setText("❌ Hasła się różnią.")
            conn.close()
            return

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')
        isadmin = self.isAdminCheckBox.isChecked()

        try:
            import os
            key_dir = "./keys"
            os.makedirs(key_dir, exist_ok=True)

            password_bytes = password.encode()
            gen = GenerateKey()
            private_key_path = f"./keys/{username}.private_key.pem"
            gen.generate_private_key(password_bytes, private_key_path)


            public_key_pem = gen.generate_public_key_from_private_key_file(private_key_path, password_bytes)

            cur.execute(
                "INSERT INTO users(username, password, isadmin, public_key) VALUES(%s, %s, %s, %s)",
                (username, hashed_password, isadmin, public_key_pem)
            )
            conn.commit()
            self.comunicatIfAdded.setText("✅ Użytkownik dodany.")
        except Exception as e:
            self.comunicatIfAdded.setText(f"❌ Błąd podczas dodawania użytkownika: {e}")
        finally:
            conn.close()

def main():
    config = load_encrypted_config()
    try:
        conn = connect_db(config["dbname"], 'adminanonchat', '123', config["host"], config["port"])
    except Exception as e:
        print(f"Błąd połączenia z bazą: {e}")
        sys.exit(1)

    username = input("Login admina: ").strip()
    password = input("Hasło: ").strip()

    cur = conn.cursor()
    cur.execute("SELECT password, isadmin FROM users WHERE username=%s", (username,))
    row = cur.fetchone()

    if not row:
        print("Nie znaleziono użytkownika.")
        sys.exit(1)

    stored_hashed_password = row['password']
    isAdmin = row['isadmin']

    if not isAdmin:
        print("Użytkownik nie jest administratorem.")
        sys.exit(1)

    if not bcrypt.checkpw(password.encode(), stored_hashed_password.encode()):
        print("Niepoprawne hasło.")
        sys.exit(1)

    app = QApplication(sys.argv)
    session = type("Session", (object,), {"username": username})()
    window = AdminWindow(session)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()