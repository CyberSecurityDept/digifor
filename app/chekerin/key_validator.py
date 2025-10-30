# key_validator.py
import os
import sys
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

def validate_private_key(key_path):
    """Validate if private key is correct X25519 key"""
    try:
        with open(key_path, 'rb') as f:
            key_data = f.read()
        
        print(f"🔍 Validating: {key_path}")
        print(f"📏 Key size: {len(key_data)} bytes")
        
        # Check size
        if len(key_data) != 32:
            print(f"❌ INVALID: Key must be 32 bytes, got {len(key_data)} bytes")
            return False
        
        # Try to load as X25519 private key
        try:
            private_key = x25519.X25519PrivateKey.from_private_bytes(key_data)
            print("✅ Private key format: VALID (X25519)")
            
            # Generate public key from private key
            public_key = private_key.public_key()
            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            
            print(f"📊 Public key derived: {public_bytes.hex()[:32]}...")
            return True
            
        except Exception as e:
            print(f"❌ INVALID: Not a valid X25519 private key - {e}")
            return False
            
    except FileNotFoundError:
        print(f"❌ File not found: {key_path}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_key_pair(private_path, public_path):
    """Test if private and public keys are a valid pair"""
    print("\n🔗 Testing Key Pair Match")
    print("=" * 40)
    
    with open(private_path, 'rb') as f:
        private_data = f.read()
    with open(public_path, 'rb') as f:
        public_data = f.read()
    
    try:
        private_key = x25519.X25519PrivateKey.from_private_bytes(private_data)
        public_key = x25519.X25519PublicKey.from_public_bytes(public_data)
        
        # Test key exchange
        shared_secret1 = private_key.exchange(public_key)
        
        print("✅ Key pair: VALID (can perform key exchange)")
        print(f"📏 Shared secret: {len(shared_secret1)} bytes")
        print(f"🔐 First 16 bytes: {shared_secret1.hex()[:32]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Key pair: INVALID - {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        private_key_file = sys.argv[1]
        public_key_file = sys.argv[2] if len(sys.argv) >= 3 else private_key_file.replace('private', 'public')
        
        if validate_private_key(private_key_file):
            if os.path.exists(public_key_file):
                test_key_pair(private_key_file, public_key_file)
    else:
        # Default files
        default_private = "mykey_private.key"
        default_public = "mykey_public.key"
        
        if os.path.exists(default_private):
            validate_private_key(default_private)
            if os.path.exists(default_public):
                test_key_pair(default_private, default_public)
        else:
            print("Usage: python3 key_validator.py <private_key_file> [public_key_file]")