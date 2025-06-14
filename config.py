from cryptography.fernet import Fernet
import json
import os

KEY_FILE = "config.key"
CONFIG_FILE = "config.json.enc"

# 1. Wygeneruj klucz AES i zapisz raz
def generate_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)

# 2. Wczytaj klucz
def load_key():
    with open(KEY_FILE, "rb") as key_file:
        return key_file.read()

# 3. Zaszyfruj i zapisz dane konfiguracyjne
def save_encrypted_config(data: dict):
    generate_key()
    key = load_key()
    fernet = Fernet(key)

    json_data = json.dumps(data).encode()
    encrypted = fernet.encrypt(json_data)

    with open(CONFIG_FILE, "wb") as f:
        f.write(encrypted)

# 4. Odszyfruj dane konfiguracyjne
def load_encrypted_config() -> dict:
    key = load_key()
    fernet = Fernet(key)

    with open(CONFIG_FILE, "rb") as f:
        encrypted = f.read()

    decrypted = fernet.decrypt(encrypted)
    return json.loads(decrypted.decode())
