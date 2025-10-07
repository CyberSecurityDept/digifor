# key_utils.py
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import os

def generate_keypair():
    """
    Generate X25519 key pair untuk encryption/decryption
    
    Returns:
        tuple: (private_key, public_key) sebagai bytes
    """
    private_key = x25519.X25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Serialize ke bytes
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    return private_bytes, public_bytes

def derive_symmetric_key(private_key, peer_public_key, salt, info=b"sdp_encryption_v1"):
    """
    Derive symmetric key menggunakan ECDH + HKDF-SHA256
    
    Args:
        private_key: X25519PrivateKey object atau bytes
        peer_public_key: X25519PublicKey object atau bytes
        salt: bytes untuk HKDF
        info: context info untuk HKDF
        
    Returns:
        bytes: 32-byte AES-256 key
    """
    # Convert bytes to key objects jika diperlukan
    if isinstance(private_key, bytes):
        private_key = x25519.X25519PrivateKey.from_private_bytes(private_key)
    if isinstance(peer_public_key, bytes):
        peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_public_key)
    
    # ECDH key exchange
    shared_secret = private_key.exchange(peer_public_key)
    
    # HKDF untuk derive AES-256 key
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # AES-256
        salt=salt,
        info=info,
        backend=default_backend()
    )
    return hkdf.derive(shared_secret)

def load_private_key(private_key_bytes):
    """Load private key dari bytes"""
    return x25519.X25519PrivateKey.from_private_bytes(private_key_bytes)

def load_public_key(public_key_bytes):
    """Load public key dari bytes"""
    return x25519.X25519PublicKey.from_public_bytes(public_key_bytes)

def generate_salt():
    """Generate random salt untuk HKDF"""
    return os.urandom(16)

def generate_nonce():
    """Generate base nonce untuk AES-GCM"""
    return os.urandom(8)  # 8 bytes untuk base, 4 bytes untuk chunk index