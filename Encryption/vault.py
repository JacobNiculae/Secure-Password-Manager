import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt_password(plaintext: str, key: bytes) -> tuple:
    iv = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode(), None)
    return iv, ciphertext

def decrypt_password(iv: bytes, ciphertext: bytes, key: bytes) -> str:
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(iv, ciphertext, None)
    return plaintext.decode()