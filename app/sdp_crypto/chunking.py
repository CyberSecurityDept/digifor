import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

class ChunkProcessor:
    def __init__(self, chunk_size=10 * 1024 * 1024):
        self.chunk_size = chunk_size
        self.sha256_hash = hashlib.sha256()
    
    def process_encrypt_chunks(self, file_path, aes_key, base_nonce):
        aesgcm = AESGCM(aes_key)
        
        with open(file_path, 'rb') as f:
            chunk_index = 0
            
            while True:
                chunk_data = f.read(self.chunk_size)
                if not chunk_data:
                    break
                
                self.sha256_hash.update(chunk_data)
                
                nonce = self._generate_chunk_nonce(base_nonce, chunk_index)
                
                encrypted_chunk = aesgcm.encrypt(nonce, chunk_data, None)
                
                yield encrypted_chunk
                chunk_index += 1
    
    def process_decrypt_chunks(self, file_path, aes_key, base_nonce, total_chunks):
        aesgcm = AESGCM(aes_key)
        self.sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk_index in range(total_chunks):
                size_bytes = f.read(4)
                if not size_bytes or len(size_bytes) != 4:
                    raise ValueError("Invalid chunk size")
                
                chunk_size = int.from_bytes(size_bytes, 'big')
                encrypted_chunk = f.read(chunk_size)
                
                if len(encrypted_chunk) != chunk_size:
                    raise ValueError("Incomplete chunk data")
                
                nonce = self._generate_chunk_nonce(base_nonce, chunk_index)
                
                try:
                    decrypted_chunk = aesgcm.decrypt(nonce, encrypted_chunk, None)
                except Exception as e:
                    raise ValueError(f"Decryption failed for chunk {chunk_index}: {str(e)}")
                
                self.sha256_hash.update(decrypted_chunk)
                
                yield decrypted_chunk
    
    def _generate_chunk_nonce(self, base_nonce, chunk_index):
        index_bytes = chunk_index.to_bytes(4, 'big')
        return base_nonce + index_bytes
    
    def get_file_hash(self):
        return self.sha256_hash.digest()