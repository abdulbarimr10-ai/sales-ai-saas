import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from app.core.config import settings

def get_encryption_key() -> bytes:
    """Returns the 32-byte encryption key from the environment."""
    key_str = settings.ENCRYPTION_KEY
    if not key_str:
        raise ValueError("ENCRYPTION_KEY is not set in the environment.")
    
    # Clean the key string
    key_str = key_str.strip().strip('"').strip("'")
    
    # 1. Try hex decoding first if it looks like a 64-character hex string
    if len(key_str) == 64:
        try:
            key = bytes.fromhex(key_str)
            if len(key) == 32:
                return key
        except ValueError:
            pass

    # 2. Try base64 decoding
    try:
        padded_key = key_str + "=" * ((4 - len(key_str) % 4) % 4)
        key = base64.urlsafe_b64decode(padded_key)
        if len(key) == 32:
            return key
    except Exception:
        pass
        
    # 3. Fallback to direct hex conversion if it didn't match the 64-char check but is valid hex
    try:
        key = bytes.fromhex(key_str)
        if len(key) == 32:
            return key
    except ValueError:
        pass
        
    raise ValueError("Invalid encryption key length/format. Must be a 32-byte key (64 hex characters or a 32-byte base64-encoded string).")

def encrypt_data(plaintext: str) -> str:
    """Encrypts plaintext string using AES-256-GCM. Returns b64 encoded string: IV + Tag + Ciphertext"""
    if not plaintext:
        return ""
        
    key = get_encryption_key()
    iv = os.urandom(12) # 96-bit IV is standard for GCM
    
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()
    tag = encryptor.tag # 16 bytes
    
    # Store IV (12) + Tag (16) + Ciphertext
    encrypted_blob = iv + tag + ciphertext
    return base64.urlsafe_b64encode(encrypted_blob).decode('utf-8')

def decrypt_data(encrypted_b64: str) -> str:
    """Decrypts b64 encoded string containing IV + Tag + Ciphertext back to plaintext."""
    if not encrypted_b64:
        return ""
        
    try:
        encrypted_blob = base64.urlsafe_b64decode(encrypted_b64)
        
        # Extract components
        iv = encrypted_blob[:12]
        tag = encrypted_blob[12:28]
        ciphertext = encrypted_blob[28:]
        
        key = get_encryption_key()
        
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        
        plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decrypt data: {str(e)}")
