# sdp_crypto/core.py
import os
import json
import base64
import hashlib
import struct
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class SDPCrypto:
    # Constants
    CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks
    HEADER_SIZE_BYTES = 4
    CHUNK_SIZE_BYTES = 4
    HASH_SIZE = 32
    
    @staticmethod
    def generate_keypair():
        """Generate X25519 key pair"""
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()
        
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

    @staticmethod
    def derive_symmetric_key(private_key, peer_public_key, salt, info=b"sdp_encryption_v1"):
        """Derive AES key using ECDH + HKDF"""
        if isinstance(private_key, bytes):
            private_key = x25519.X25519PrivateKey.from_private_bytes(private_key)
        if isinstance(peer_public_key, bytes):
            peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_public_key)
        
        shared_secret = private_key.exchange(peer_public_key)
        
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # AES-256
            salt=salt,
            info=info,
            backend=default_backend()
        )
        return hkdf.derive(shared_secret)

    @staticmethod
    def encrypt_to_sdp(recipient_public_key, input_path, output_path, chunk_size=None):
        """
        Encrypt any file to .sdp format - No size limits
        
        Args:
            recipient_public_key: Public key bytes
            input_path: Input file path
            output_path: Output .sdp path
            chunk_size: Chunk size in bytes (default: 10MB)
        """
        if chunk_size is None:
            chunk_size = SDPCrypto.CHUNK_SIZE
            
        # Input validation
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if not recipient_public_key or len(recipient_public_key) != 32:
            raise ValueError("Invalid recipient public key (must be 32 bytes)")
        
        # Generate ephemeral keys
        ephemeral_private, ephemeral_public = SDPCrypto.generate_keypair()
        
        # Generate crypto parameters
        salt = os.urandom(16)
        base_nonce = os.urandom(8)  # 8 bytes base, 4 bytes for chunk index
        
        # Derive AES key
        aes_key = SDPCrypto.derive_symmetric_key(ephemeral_private, recipient_public_key, salt)
        aesgcm = AESGCM(aes_key)
        
        # Get file info
        file_size = os.path.getsize(input_path)
        filename = os.path.basename(input_path)
        
        # Create header
        header = {
            "version": "2.0",
            "filename": filename,
            "file_size": file_size,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ephemeral_public_key": base64.b64encode(ephemeral_public).decode('ascii'),
            "salt": base64.b64encode(salt).decode('ascii'),
            "base_nonce": base64.b64encode(base_nonce).decode('ascii'),
            "chunk_size": chunk_size,
            "algorithm": "X25519+AES-GCM-256",
            "total_chunks": (file_size + chunk_size - 1) // chunk_size  # Ceiling division
        }
        
        header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
        
        # Process encryption
        sha256_hash = hashlib.sha256()
        
        with open(input_path, 'rb') as infile, open(output_path, 'wb') as outfile:
            # Write header length + header
            outfile.write(len(header_json).to_bytes(SDPCrypto.HEADER_SIZE_BYTES, 'big'))
            outfile.write(header_json)
            
            # Encrypt file in chunks
            chunk_index = 0
            bytes_processed = 0
            
            while True:
                chunk_data = infile.read(chunk_size)
                if not chunk_data:
                    break
                
                # Update hash of original data
                sha256_hash.update(chunk_data)
                
                # Generate unique nonce for this chunk
                nonce = base_nonce + chunk_index.to_bytes(4, 'big')
                
                # Encrypt chunk
                encrypted_chunk = aesgcm.encrypt(nonce, chunk_data, None)
                
                # Write chunk size + encrypted data
                outfile.write(len(encrypted_chunk).to_bytes(SDPCrypto.CHUNK_SIZE_BYTES, 'big'))
                outfile.write(encrypted_chunk)
                
                chunk_index += 1
                bytes_processed += len(chunk_data)
                
                # Progress for large files (optional)
                if file_size > 100 * 1024 * 1024:  # Only for files > 100MB
                    progress = (bytes_processed / file_size) * 100
                    if chunk_index % 10 == 0:  # Print every 10 chunks
                        print(f"Encrypted: {bytes_processed}/{file_size} bytes ({progress:.1f}%)")
            
            # Write original file hash as footer
            original_hash = sha256_hash.digest()
            outfile.write(original_hash)
            
            print(f"✅ Encryption complete: {chunk_index} chunks processed")
            print(f"📊 Original size: {file_size:,} bytes")
            print(f"🔐 Encrypted size: {os.path.getsize(output_path):,} bytes")

    @staticmethod
    def decrypt_from_sdp(recipient_private_key, input_path, output_dir=None):
        """
        Decrypt .sdp file to original file - No size limits
        
        Args:
            recipient_private_key: Private key bytes
            input_path: Input .sdp path
            output_dir: Output directory (optional)
            
        Returns:
            str: Path to decrypted file
        """
        # Input validation
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"SDP file not found: {input_path}")
        
        if not recipient_private_key or len(recipient_private_key) != 32:
            raise ValueError("Invalid recipient private key (must be 32 bytes)")
        
        with open(input_path, 'rb') as infile:
            # Read and parse header
            try:
                header_len_bytes = infile.read(SDPCrypto.HEADER_SIZE_BYTES)
                if len(header_len_bytes) != SDPCrypto.HEADER_SIZE_BYTES:
                    raise ValueError("Invalid SDP file: missing header length")
                
                header_len = int.from_bytes(header_len_bytes, 'big')
                header_json = infile.read(header_len)
                
                if len(header_json) != header_len:
                    raise ValueError("Invalid SDP file: incomplete header")
                
                header = json.loads(header_json.decode('utf-8'))
                
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                raise ValueError(f"Invalid SDP header: {str(e)}")
            
            # Validate header
            required_fields = ['filename', 'ephemeral_public_key', 'salt', 'base_nonce', 'chunk_size']
            for field in required_fields:
                if field not in header:
                    raise ValueError(f"Missing required field in header: {field}")
            
            # Get crypto parameters
            ephemeral_public = base64.b64decode(header['ephemeral_public_key'])
            salt = base64.b64decode(header['salt'])
            base_nonce = base64.b64decode(header['base_nonce'])
            chunk_size = header['chunk_size']
            
            # Derive AES key
            aes_key = SDPCrypto.derive_symmetric_key(recipient_private_key, ephemeral_public, salt)
            aesgcm = AESGCM(aes_key)
            
            # Determine output path
            if output_dir is None:
                output_dir = os.path.dirname(input_path) or '.'
            
            os.makedirs(output_dir, exist_ok=True)
            output_filename = header['filename']
            output_path = os.path.join(output_dir, output_filename)
            
            # Handle filename conflicts
            counter = 1
            original_output_path = output_path
            while os.path.exists(output_path):
                name, ext = os.path.splitext(original_output_path)
                output_path = f"{name}_{counter}{ext}"
                counter += 1
            
            # Get file size for progress tracking
            file_size = os.path.getsize(input_path)
            header_total_size = SDPCrypto.HEADER_SIZE_BYTES + header_len
            
            # Process decryption
            sha256_hash = hashlib.sha256()
            
            with open(output_path, 'wb') as outfile:
                chunk_index = 0
                bytes_processed = 0
                total_chunks = header.get('total_chunks', 0)
                
                # Read until we reach the footer (last 32 bytes)
                while infile.tell() < file_size - SDPCrypto.HASH_SIZE:
                    # Read chunk size
                    chunk_size_bytes = infile.read(SDPCrypto.CHUNK_SIZE_BYTES)
                    if not chunk_size_bytes or len(chunk_size_bytes) != SDPCrypto.CHUNK_SIZE_BYTES:
                        break
                    
                    chunk_data_size = int.from_bytes(chunk_size_bytes, 'big')
                    
                    # Read encrypted chunk
                    encrypted_chunk = infile.read(chunk_data_size)
                    if len(encrypted_chunk) != chunk_data_size:
                        raise ValueError(f"Incomplete chunk data at position {infile.tell()}")
                    
                    # Generate nonce
                    nonce = base_nonce + chunk_index.to_bytes(4, 'big')
                    
                    # Decrypt chunk
                    try:
                        decrypted_chunk = aesgcm.decrypt(nonce, encrypted_chunk, None)
                    except Exception as e:
                        raise ValueError(f"Decryption failed for chunk {chunk_index}: {str(e)}")
                    
                    # Write decrypted data and update hash
                    outfile.write(decrypted_chunk)
                    sha256_hash.update(decrypted_chunk)
                    
                    chunk_index += 1
                    bytes_processed += len(decrypted_chunk)
                    
                    # Progress for large files (optional)
                    if header.get('file_size', 0) > 100 * 1024 * 1024:  # Only for files > 100MB
                        progress = (bytes_processed / header['file_size']) * 100
                        if chunk_index % 10 == 0:  # Print every 10 chunks
                            print(f"Decrypted: {bytes_processed}/{header['file_size']} bytes ({progress:.1f}%)")
                
                print(f"✅ Decryption complete: {chunk_index} chunks processed")
            
            # Verify integrity
            current_pos = infile.tell()
            infile.seek(-SDPCrypto.HASH_SIZE, 2)  # Seek to footer
            original_hash = infile.read(SDPCrypto.HASH_SIZE)
            
            decrypted_hash = sha256_hash.digest()
            
            if decrypted_hash != original_hash:
                # Clean up corrupted file
                if os.path.exists(output_path):
                    os.remove(output_path)
                raise ValueError("❌ Integrity check failed: SHA256 hash mismatch")
            
            print("✅ Integrity verification: SHA256 hash matches")
            
            # Verify file size if available in header
            if 'file_size' in header:
                decrypted_size = os.path.getsize(output_path)
                if decrypted_size != header['file_size']:
                    print(f"⚠️  Warning: File size mismatch. Expected: {header['file_size']}, Got: {decrypted_size}")
            
            return output_path