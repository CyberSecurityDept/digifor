import json, struct, base64, os
from datetime import datetime

class SDPHeader:
    def __init__(self, filename, file_size, ephemeral_public_key, salt, 
                 base_nonce, chunk_size=10 * 1024 * 1024):
        self.version = "1.0"
        self.filename = filename
        self.file_size = file_size
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.ephemeral_public_key = base64.b64encode(ephemeral_public_key).decode('ascii')
        self.salt = base64.b64encode(salt).decode('ascii')
        self.base_nonce = base64.b64encode(base_nonce).decode('ascii')
        self.chunk_size = chunk_size
        self.algorithm = "X25519+AES-GCM"
    
    def to_dict(self):
        return {
            "version": self.version,
            "filename": self.filename,
            "file_size": self.file_size,
            "timestamp": self.timestamp,
            "ephemeral_public_key": self.ephemeral_public_key,
            "salt": self.salt,
            "base_nonce": self.base_nonce,
            "chunk_size": self.chunk_size,
            "algorithm": self.algorithm
        }
    
    def to_json(self):
        return json.dumps(self.to_dict(), separators=(',', ':'))
    
    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        header = cls(
            filename=data["filename"],
            file_size=data["file_size"],
            ephemeral_public_key=base64.b64decode(data["ephemeral_public_key"]),
            salt=base64.b64decode(data["salt"]),
            base_nonce=base64.b64decode(data["base_nonce"]),
            chunk_size=data["chunk_size"]
        )
        header.version = data.get("version", "1.0")
        header.timestamp = data.get("timestamp")
        header.algorithm = data.get("algorithm", "X25519+AES-GCM")
        return header

class SDPFile:
    @staticmethod
    def write_header(f, header_json):
        header_bytes = header_json.encode('utf-8')
        header_len = len(header_bytes)
        
        f.write(header_len.to_bytes(4, 'big'))
        f.write(header_bytes)
    
    @staticmethod
    def read_header(f):
        header_len_bytes = f.read(4)
        if len(header_len_bytes) != 4:
            raise ValueError("Invalid SDP file: missing header length")
        
        header_len = int.from_bytes(header_len_bytes, 'big')
        
        header_json_bytes = f.read(header_len)
        if len(header_json_bytes) != header_len:
            raise ValueError("Invalid SDP file: incomplete header")
        
        return header_json_bytes.decode('utf-8')
    
    @staticmethod
    def write_chunk(f, encrypted_chunk):
        chunk_size = len(encrypted_chunk)
        f.write(chunk_size.to_bytes(4, 'big'))
        f.write(encrypted_chunk)
    
    @staticmethod
    def write_footer(f, original_hash):
        f.write(original_hash)