import psycopg2
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

class ChatDB:
    def __init__(self, dbname, user, password, host, port):
        self.conn = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host, port=port
        )

    def create_chat(self, name: str, member_ids: list[int]):
        with self.conn.cursor() as cur:
            cur.execute("INSERT INTO chats (name) VALUES (%s) RETURNING id", (name,))
            chat_id = cur.fetchone()[0]

            for user_id in member_ids:
                cur.execute(
                    "INSERT INTO chat_members (chat_id, user_id) VALUES (%s, %s)",
                    (chat_id, user_id),
                )
            self.conn.commit()
            return chat_id

    def add_message(self, chat_id: int, sender_id: int, receiver_id: int, encrypted_message: bytes):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages (chat_id, sender_id, receiver_id, encrypted_message) VALUES (%s, %s, %s, %s)",
                (chat_id, sender_id, receiver_id, encrypted_message),
            )
            self.conn.commit()


    def get_messages(self, chat_id: int):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT sender_id, encrypted_message, timestamp
                FROM messages
                WHERE chat_id = %s
                ORDER BY timestamp ASC
                """,
                (chat_id,),
            )
            return cur.fetchall()

    def get_public_key(self, user_id: int) -> bytes:
        with self.conn.cursor() as cur:
            cur.execute("SELECT public_key FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return row[0] if row else None

    def get_chat_members(self, chat_id: int):
        with self.conn.cursor() as cur:
            cur.execute("SELECT user_id FROM chat_members WHERE chat_id = %s", (chat_id,))
            rows = cur.fetchall()
            return [row[0] for row in rows]

    def close(self):
        self.conn.close()
        
        
    def get_or_create_chat(self, user_id1, user_id2):
        cur = self.conn.cursor()

        # Szukamy czatu z dokładnie tymi dwoma użytkownikami
        cur.execute("""
            SELECT c.id
            FROM chats c
            JOIN chat_members cm ON c.id = cm.chat_id
            GROUP BY c.id
            HAVING COUNT(*) = 2 AND bool_and(cm.user_id IN (%s, %s))
            LIMIT 1;
        """, (user_id1, user_id2))

        row = cur.fetchone()
        if row:
            chat_id = row['id']
        else:
            # Stwórz nowy czat
            cur.execute("INSERT INTO chats DEFAULT VALUES RETURNING id;")
            chat_id = cur.fetchone()['id']

            cur.execute("INSERT INTO chat_members (chat_id, user_id) VALUES (%s, %s), (%s, %s);",
                        (chat_id, user_id1, chat_id, user_id2))
            self.conn.commit()

        cur.close()
        return chat_id

