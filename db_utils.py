import psycopg2

def save_encrypted_message(conn, chat_id, sender_id, receiver_id, encrypted_bytes):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO messages (chat_id, sender_id, receiver_id, encrypted_message)
            VALUES (%s, %s, %s, %s)
        """, (chat_id, sender_id, receiver_id, psycopg2.Binary(encrypted_bytes)))
    conn.commit()

def get_encrypted_messages(conn, chat_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT sender_id, receiver_id, encrypted_message FROM messages
            WHERE chat_id = %s ORDER BY id ASC
        """, (chat_id,))
        return cur.fetchall()

def get_user_public_key(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("SELECT public_key FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if row:
            return row['public_key'].encode('utf-8')  # PEM jako bytes
        else:
            raise Exception("Public key not found")
