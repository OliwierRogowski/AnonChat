# crypto_utils.py
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

class Messages:
    def __init__(self, private_key=None, public_key=None, password: bytes = None):
        self.private_key = private_key
        self.public_key = public_key
        self.password = password

    def load_private_key(self, filename="anonChat.pem"):
        with open(filename, "rb") as f:
            pem_data = f.read()
        self.private_key = serialization.load_pem_private_key(pem_data, password=self.password)
        self.public_key = self.private_key.public_key()
        
        
    def load_public_key(self, pem_data: bytes):
        self.public_key = serialization.load_pem_public_key(pem_data)

    def encrypt_message(self, message: bytes) -> bytes:
        if self.public_key is None:
            raise ValueError("Public key not loaded")
        return self.public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        
    def decrypt_message(self, encrypted_message) -> bytes:
        if self.private_key is None:
            raise ValueError("Brak załadowanego klucza prywatnego")
        
        # Konwersja memoryview -> bytes, jeśli potrzeba
        if isinstance(encrypted_message, memoryview):
            encrypted_message = encrypted_message.tobytes()

        return self.private_key.decrypt(
            encrypted_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
