# chunking.py
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

class ChunkProcessor:
    def __init__(self, chunk_size=10 * 1024 * 1024):  # 10MB default
        self.chunk_size = chunk_size
        self.sha256_hash = hashlib.sha256()
    
    def process_encrypt_chunks(self, file_path, aes_key, base_nonce):
        """Encrypt file per chunk dan update hash"""
        aesgcm = AESGCM(aes_key)
        
        with open(file_path, 'rb') as f:
            chunk_index = 0
            
            while True:
                chunk_data = f.read(self.chunk_size)
                if not chunk_data:
                    break
                
                # Update hash file asli
                self.sha256_hash.update(chunk_data)
                
                # Generate unique nonce untuk chunk ini
                nonce = self._generate_chunk_nonce(base_nonce, chunk_index)
                
                # Encrypt chunk dengan AES-GCM
                encrypted_chunk = aesgcm.encrypt(nonce, chunk_data, None)
                
                yield encrypted_chunk
                chunk_index += 1
    
    def process_decrypt_chunks(self, file_path, aes_key, base_nonce, total_chunks):
        """Decrypt file per chunk dan update hash"""
        aesgcm = AESGCM(aes_key)
        self.sha256_hash = hashlib.sha256()  # Reset untuk verification
        
        with open(file_path, 'rb') as f:
            for chunk_index in range(total_chunks):
                # Read chunk size (4 bytes) + encrypted data
                size_bytes = f.read(4)
                if not size_bytes or len(size_bytes) != 4:
                    raise ValueError("Invalid chunk size")
                
                chunk_size = int.from_bytes(size_bytes, 'big')
                encrypted_chunk = f.read(chunk_size)
                
                if len(encrypted_chunk) != chunk_size:
                    raise ValueError("Incomplete chunk data")
                
                # Generate unique nonce
                nonce = self._generate_chunk_nonce(base_nonce, chunk_index)
                
                try:
                    # Decrypt chunk
                    decrypted_chunk = aesgcm.decrypt(nonce, encrypted_chunk, None)
                except Exception as e:
                    raise ValueError(f"Decryption failed for chunk {chunk_index}: {str(e)}")
                
                # Update hash untuk integrity check
                self.sha256_hash.update(decrypted_chunk)
                
                yield decrypted_chunk
    
    def _generate_chunk_nonce(self, base_nonce, chunk_index):
        """Generate unique nonce untuk setiap chunk"""
        # Nonce = base_nonce (8 bytes) + chunk_index (4 bytes)
        index_bytes = chunk_index.to_bytes(4, 'big')
        return base_nonce + index_bytes
    
    def get_file_hash(self):
        """Get final SHA256 hash"""
        return self.sha256_hash.digest()