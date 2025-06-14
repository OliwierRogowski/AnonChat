from messages import Messages
from db_utils import save_encrypted_message, get_encrypted_messages, get_user_public_key
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding


class ChatHandler:
    def __init__(self, conn, private_key_password: bytes, private_key_file=None, keys_dir="user_keys"):
        self.conn = conn
        self.crypto = Messages(password=private_key_password)
        self.keys_dir = keys_dir

        if private_key_file:
            self.crypto.load_private_key(private_key_file)

    def load_private_key_for_user(self, username):
        private_key_path = f"/home/yeti/Pulpit/Programy/anonChat/keys/{username}.private_key.pem"
        self.crypto.load_private_key(private_key_path)

    def send_message(self, chat_id, sender_id, receiver_id, message_text):
        cur = self.conn.cursor()

        cur.execute("SELECT public_key FROM users WHERE id = %s;", (receiver_id,))
        row = cur.fetchone()
        if not row or not row['public_key']:
            raise Exception("Publiczny klucz odbiorcy nie znaleziony")

        public_key_pem = row['public_key']
        public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))

        encrypted_message = public_key.encrypt(
            message_text.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        cur.execute("""
            INSERT INTO messages (chat_id, sender_id, receiver_id, encrypted_message)
            VALUES (%s, %s, %s, %s);
        """, (chat_id, sender_id, receiver_id, encrypted_message))

        self.conn.commit()
        cur.close()

    def read_chat(self, chat_id, current_user_id, username=None):
        
        messages = []
        try:
            # Załaduj klucz prywatny dla current_user_id
            self.load_private_key_for_user(username)

            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT sender_id, receiver_id, encrypted_message FROM messages WHERE chat_id = %s ORDER BY timestamp",
                    (chat_id,)
                )
                rows = cur.fetchall()

                for row in rows:
                    sender_id = row['sender_id']
                    receiver_id = row['receiver_id']
                    encrypted_bytes = bytes(row['encrypted_message'])

                    if receiver_id == current_user_id:
                        try:
                            decrypted_bytes = self.crypto.decrypt_message(encrypted_bytes)
                            decrypted_text = decrypted_bytes.decode('utf-8')
                        except Exception as e:
                            decrypted_text = "[Błąd odszyfrowania]"
                            print(f"Błąd odszyfrowania: {e}")
                    else:
                        decrypted_text = "[Wiadomość zaszyfrowana dla innego użytkownika]"
                    messages.append((sender_id, receiver_id, decrypted_text))

        except Exception as e:
            print(f"Błąd podczas odczytu czatu: {e}")
        return messages