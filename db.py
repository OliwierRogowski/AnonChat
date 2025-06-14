import psycopg2
from psycopg2.extras import RealDictCursor
from keyring_utils import load_password
from config import load_encrypted_config


def connect_db(dbname, user, password, host, port):
    config = load_encrypted_config()
    password = load_password(config["user"])
    
    if not password:
        raise Exception("Brak hasła w keyring")
    
    conn = psycopg2.connect(
        dbname=config["dbname"],
        user=config["user"],
        password=password,
        host=config["host"],
        port=config["port"],
        cursor_factory=RealDictCursor
    )
    return conn


