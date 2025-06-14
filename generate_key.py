import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class GenerateKey:
    def __init__(self):
            self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            self.public_key = self.private_key.public_key()

    def generate_public_key(self) -> str:
        pem_public = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem_public.decode('utf-8')

    def generate_private_key(self, password_to_file_with_key: bytes, filepath: str):
        directory = os.path.dirname(filepath)
        os.makedirs(directory, exist_ok=True)

        with open(filepath, "wb") as f:
            f.write(
                self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.BestAvailableEncryption(password_to_file_with_key)
                )
            )
        print(f"Klucz prywatny zapisany w: {filepath}")
        return filepath

    def generate_public_key_from_private_key_file(self, private_key_path: str, password: bytes = None) -> str:
        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=password,
            )
        public_key = private_key.public_key()
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem_public.decode('utf-8')