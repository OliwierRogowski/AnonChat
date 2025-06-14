from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QLabel, QLineEdit, QWidget, 
    QPushButton, QMessageBox, QHBoxLayout,
    QListWidget, QTextBrowser, QListWidgetItem
)
from PyQt6.QtCore import Qt
import psycopg2
from db import connect_db 
class MessageWindow(QWidget):
    def __init__(self, chat_handler, chat_id, user_id1, user_id2):
        super().__init__()
        self.chat_handler = chat_handler
        self.chat_id = chat_id
        self.user_id1 = user_id1
        self.user_id2 = user_id2

        self.setWindowTitle(f"Czat: {user_id1} <> {user_id2}")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.text_browser = QTextBrowser()
        layout.addWidget(self.text_browser)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Napisz wiadomość...")
        layout.addWidget(self.input_line)

        self.send_button = QPushButton("Wyślij")
        layout.addWidget(self.send_button)

        # Poprawne podpięcie: metoda bez argumentów, wywołuje wewnątrz send_message ChatHandlera z argumentami
        self.send_button.clicked.connect(self.send_message)

        self.load_chat()

    def load_chat(self):
        self.text_browser.clear()
        conn = connect_db("anonChatDb", "adminanonchat", "123", "localhost", "5432")
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE id = %s", (self.user_id1,))
        username = cur.fetchone()['username']
        conn.close()
        messages = self.chat_handler.read_chat(self.chat_id, self.user_id1, username )
        for sender_id, receiver_id, message_text in messages:
            sender = "Ty" if sender_id == self.user_id1 else f"Użytkownik {sender_id}"
            self.text_browser.append(f"<b>{sender}:</b> {message_text}")

    def send_message(self):
        text = self.input_line.text().strip()
        if not text:
            return
        # Tu wywołujemy metodę ChatHandler z argumentami
        self.chat_handler.send_message(self.chat_id, self.user_id1, self.user_id2, text)
        self.input_line.clear()
        self.load_chat()



class ChatWindow(QMainWindow):
    def __init__(self, session, conn, chat_handler, private_key_password):
        super().__init__()
        self.session = session
        self.conn = conn
        self.chat_handler = chat_handler

        self.setWindowTitle(f"AnonChat - Chat {self.session.username}")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Lewy panel z listą użytkowników i wyszukiwarką
        self.left_panel = QWidget()
        left_layout = QVBoxLayout()
        self.left_panel.setLayout(left_layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Szukaj użytkownika...")
        self.search_input.textChanged.connect(self.filter_users)
        left_layout.addWidget(self.search_input)

        self.user_list = QListWidget()
        self.user_list.currentRowChanged.connect(self.user_selected)
        left_layout.addWidget(self.user_list)

        main_layout.addWidget(self.left_panel, 1)

        # Prawy panel na okno czatu
        self.message_area = QWidget()
        self.message_layout = QVBoxLayout()
        self.message_area.setLayout(self.message_layout)
        main_layout.addWidget(self.message_area, 4)

        self.users = self.load_users()
        self.populate_user_list()

        self.current_chat_window = None

    def load_users(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, username FROM users WHERE username != %s;", (self.session.username,))
        rows = cur.fetchall()
        return {row['id']: row['username'] for row in rows}

    def populate_user_list(self):
        self.user_list.clear()
        for user_id, username in self.users.items():
            item = QListWidgetItem(username)
            item.setData(Qt.ItemDataRole.UserRole, user_id)
            self.user_list.addItem(item)

    def filter_users(self, text):
        text = text.lower()
        for i in range(self.user_list.count()):
            item = self.user_list.item(i)
            item.setHidden(text not in item.text().lower())

    def user_selected(self, index):
        if index < 0:
            return

        item = self.user_list.item(index)
        user_id = item.data(Qt.ItemDataRole.UserRole)

        chat_id = self.get_or_create_chat(self.session.user_id, user_id)

        # Usuń stare okno czatu
        if self.current_chat_window:
            self.message_layout.removeWidget(self.current_chat_window)
            self.current_chat_window.deleteLater()
            self.current_chat_window = None

        # Utwórz nowe okno czatu
        self.current_chat_window = MessageWindow(self.chat_handler, chat_id, self.session.user_id, user_id)
        self.message_layout.addWidget(self.current_chat_window)

    def get_or_create_chat(self, user_id1, user_id2):
        cur = self.conn.cursor()

        # Znajdź czat z dokładnie tymi dwoma użytkownikami i żadnym innym
        cur.execute("""
            SELECT c.id
            FROM chats c
            JOIN chat_members cm ON c.id = cm.chat_id
            GROUP BY c.id
            HAVING 
                COUNT(*) = 2 
                AND bool_and(cm.user_id IN (%s, %s))
            LIMIT 1;
        """, (user_id1, user_id2))

        row = cur.fetchone()
        if row:
            chat_id = row['id']
        else:
            # Stwórz nowy czat
            cur.execute("INSERT INTO chats DEFAULT VALUES RETURNING id;")
            chat_id = cur.fetchone()['id']

            # Dodaj członków
            cur.execute("INSERT INTO chat_members (chat_id, user_id) VALUES (%s, %s), (%s, %s);",
                        (chat_id, user_id1, chat_id, user_id2))
            self.conn.commit()

        cur.close()
        return chat_id
