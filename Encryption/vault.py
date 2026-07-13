import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt(plaintexts: list[str], key: bytes) -> list[tuple[bytes, bytes]]:
    aesgcm = AESGCM(key)
    result = []
    for plaintext in plaintexts:
        iv = os.urandom(12)  # fresh IV per field — never reuse with AES-GCM
        ciphertext = aesgcm.encrypt(iv, plaintext.encode(), None)
        result.append((iv, ciphertext))
    return result

#iv, ciphertext

def decrypt(iv: bytes, ciphertext: bytes, key: bytes) -> str:
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(iv, ciphertext, None)
    return plaintext.decode() 