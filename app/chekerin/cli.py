# cli.py
import argparse
import sys
import os
import json
import struct
import glob
from sdp_crypto import generate_keypair, encrypt_to_sdp, decrypt_from_sdp

def is_sdp_encrypted(file_path):
    """
    Check if file is SDP encrypted
    Returns: True if encrypted, False if not, None if error
    """
    try:
        if not os.path.exists(file_path):
            return False
            
        file_size = os.path.getsize(file_path)
        if file_size < 40:  # Minimum SDP file size
            return False
            
        with open(file_path, 'rb') as f:
            # Read header length
            header_len_bytes = f.read(4)
            if len(header_len_bytes) != 4:
                return False
                
            header_len = struct.unpack('>I', header_len_bytes)[0]
            
            # Read header JSON
            header_json = f.read(header_len)
            if len(header_json) != header_len:
                return False
                
            # Try to parse JSON header
            try:
                header = json.loads(header_json.decode('utf-8'))
                
                # Check for SDP signature fields
                required_fields = ['version', 'filename', 'ephemeral_public_key', 'salt', 'algorithm']
                if all(field in header for field in required_fields):
                    return True
                else:
                    return False
                    
            except (json.JSONDecodeError, UnicodeDecodeError):
                return False
                
    except Exception:
        return False

def get_sdp_file_info(file_path):
    """Get detailed info about SDP encrypted file"""
    if not is_sdp_encrypted(file_path):
        return None
        
    try:
        with open(file_path, 'rb') as f:
            header_len = struct.unpack('>I', f.read(4))[0]
            header_json = f.read(header_len)
            header = json.loads(header_json.decode('utf-8'))
            
            # Get file size info
            file_size = os.path.getsize(file_path)
            header_size = 4 + header_len
            footer_size = 32  # SHA256 hash
            
            # Estimate data size
            data_size = file_size - header_size - footer_size
            
            return {
                'filename': header.get('filename', 'Unknown'),
                'original_size': header.get('file_size', 0),
                'encrypted_size': file_size,
                'algorithm': header.get('algorithm', 'Unknown'),
                'timestamp': header.get('timestamp', 'Unknown'),
                'chunk_size': header.get('chunk_size', 0),
                'total_chunks': header.get('total_chunks', 0),
                'header_size': header_size,
                'data_size': data_size,
                'footer_size': footer_size
            }
    except Exception as e:
        return None

def check_files_in_directory(directory='.'):
    """Check all files in directory for encryption status"""
    print(f"🔍 Checking encryption status in: {os.path.abspath(directory)}")
    print("=" * 60)
    
    files = os.listdir(directory)
    results = []
    
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            is_encrypted = is_sdp_encrypted(file_path)
            status = "✅ ENCRYPTED" if is_encrypted else "❌ NOT ENCRYPTED"
            results.append((file, status, file_path))
    
def encrypt_multiple_files(public_key_path, file_patterns, output_dir=None):
    """Encrypt multiple files matching patterns"""
    with open(public_key_path, 'rb') as f:
        pub_key = f.read()
    
    encrypted_files = []
    
    for pattern in file_patterns:
        matched_files = glob.glob(pattern)
        if not matched_files:
            print(f"⚠️  No files found matching: {pattern}")
            continue
            
        for file_path in matched_files:
            if os.path.isfile(file_path):
                try:
                    if output_dir:
                        # Create output directory if it doesn't exist
                        os.makedirs(output_dir, exist_ok=True)
                        output_file = os.path.join(output_dir, os.path.basename(file_path) + '.sdp')
                    else:
                        output_file = file_path + '.sdp'
                    
                    encrypt_to_sdp(pub_key, file_path, output_file)
                    encrypted_files.append((file_path, output_file))
                    print(f"✅ Encrypted: {file_path} -> {output_file}")
                    
                except Exception as e:
                    print(f"❌ Failed to encrypt {file_path}: {e}")
    
    return encrypted_files

def decrypt_multiple_files(private_key_path, sdp_patterns, output_dir='.'):
    """Decrypt multiple .sdp files matching patterns"""
    with open(private_key_path, 'rb') as f:
        priv_key = f.read()
    
    decrypted_files = []
    
    for pattern in sdp_patterns:
        matched_files = glob.glob(pattern)
        if not matched_files:
            print(f"⚠️  No files found matching: {pattern}")
            continue
            
        for file_path in matched_files:
            if os.path.isfile(file_path) and file_path.endswith('.sdp'):
                try:
                    decrypted_path = decrypt_from_sdp(priv_key, file_path, output_dir)
                    decrypted_files.append((file_path, decrypted_path))
                    print(f"✅ Decrypted: {file_path} -> {decrypted_path}")
                    
                except Exception as e:
                    print(f"❌ Failed to decrypt {file_path}: {e}")
    
    return decrypted_files

def encrypt_folder(public_key_path, folder_path, output_dir=None, recursive=False):
    """Encrypt semua files dalam folder"""
    with open(public_key_path, 'rb') as f:
        pub_key = f.read()
    
    # Normalize path
    folder_path = os.path.abspath(folder_path)
    
    if not os.path.exists(folder_path):
        print(f"❌ Folder tidak ditemukan: {folder_path}")
        return []
    
    if not os.path.isdir(folder_path):
        print(f"❌ Path bukan folder: {folder_path}")
        return []
    
    # Determine output directory
    if output_dir is None:
        output_dir = folder_path + "_encrypted"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📁 Encrypting folder: {folder_path}")
    print(f"📂 Output directory: {output_dir}")
    print(f"🔍 Recursive: {'Yes' if recursive else 'No'}")
    print("=" * 50)
    
    encrypted_files = []
    
    # Collect all files
    if recursive:
        pattern = os.path.join(folder_path, "**", "*")
    else:
        pattern = os.path.join(folder_path, "*")
    
    all_files = glob.glob(pattern, recursive=recursive)
    file_count = sum(1 for f in all_files if os.path.isfile(f))
    
    print(f"📊 Found {file_count} files to encrypt")
    
    for i, file_path in enumerate(all_files, 1):
        if os.path.isfile(file_path):
            try:
                # Skip .sdp files to avoid re-encrypting
                if file_path.endswith('.sdp'):
                    continue
                
                # Calculate relative path for output structure
                if recursive:
                    relative_path = os.path.relpath(file_path, folder_path)
                    file_output_dir = os.path.join(output_dir, os.path.dirname(relative_path))
                else:
                    relative_path = os.path.basename(file_path)
                    file_output_dir = output_dir
                
                # Create subdirectories if needed
                os.makedirs(file_output_dir, exist_ok=True)
                
                output_file = os.path.join(file_output_dir, relative_path + '.sdp')
                
                # Encrypt file
                encrypt_to_sdp(pub_key, file_path, output_file)
                encrypted_files.append((file_path, output_file))
                
                print(f"✅ [{i}/{file_count}] Encrypted: {relative_path}")
                
            except Exception as e:
                print(f"❌ [{i}/{file_count}] Failed to encrypt {file_path}: {e}")
    
    print(f"\n📊 Summary: {len(encrypted_files)} files encrypted successfully")
    return encrypted_files

def decrypt_folder(private_key_path, folder_path, output_dir=None, recursive=False):
    """Decrypt semua .sdp files dalam folder"""
    with open(private_key_path, 'rb') as f:
        priv_key = f.read()
    
    # Normalize path
    folder_path = os.path.abspath(folder_path)
    
    if not os.path.exists(folder_path):
        print(f"❌ Folder tidak ditemukan: {folder_path}")
        return []
    
    # Determine output directory
    if output_dir is None:
        output_dir = folder_path + "_decrypted"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📁 Decrypting folder: {folder_path}")
    print(f"📂 Output directory: {output_dir}")
    print(f"🔍 Recursive: {'Yes' if recursive else 'No'}")
    print("=" * 50)
    
    decrypted_files = []
    
    # Collect all .sdp files
    if recursive:
        pattern = os.path.join(folder_path, "**", "*.sdp")
    else:
        pattern = os.path.join(folder_path, "*.sdp")
    
    sdp_files = glob.glob(pattern, recursive=recursive)
    
    print(f"📊 Found {len(sdp_files)} .sdp files to decrypt")
    
    for i, sdp_file in enumerate(sdp_files, 1):
        try:
            # Calculate relative path for output structure
            if recursive:
                relative_path = os.path.relpath(sdp_file, folder_path)
                # Remove .sdp extension and get directory
                relative_path_no_ext = relative_path[:-4]  # Remove .sdp
                file_output_dir = os.path.join(output_dir, os.path.dirname(relative_path_no_ext))
            else:
                relative_path = os.path.basename(sdp_file)
                relative_path_no_ext = relative_path[:-4]  # Remove .sdp
                file_output_dir = output_dir
            
            # Create subdirectories if needed
            os.makedirs(file_output_dir, exist_ok=True)
            
            # Decrypt file
            decrypted_path = decrypt_from_sdp(priv_key, sdp_file, file_output_dir)
            decrypted_files.append((sdp_file, decrypted_path))
            
            print(f"✅ [{i}/{len(sdp_files)}] Decrypted: {relative_path}")
            
        except Exception as e:
            print(f"❌ [{i}/{len(sdp_files)}] Failed to decrypt {sdp_file}: {e}")
    
    print(f"\n📊 Summary: {len(decrypted_files)} files decrypted successfully")
    return decrypted_files

def main():
    parser = argparse.ArgumentParser(description="SDP Crypto - File Encryption Tool")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Generate keys command
    key_parser = subparsers.add_parser('generate-keys', help='Generate key pair')
    key_parser.add_argument('--name', default='mykey', help='Key name prefix')
    
    # Encrypt command (single file)
    encrypt_parser = subparsers.add_parser('encrypt', help='Encrypt a file')
    encrypt_parser.add_argument('file', help='File to encrypt')
    encrypt_parser.add_argument('--public-key', required=True, help='Public key file')
    encrypt_parser.add_argument('--output', help='Output .sdp file')
    
    # Encrypt-multiple command
    encrypt_multi_parser = subparsers.add_parser('encrypt-multiple', help='Encrypt multiple files')
    encrypt_multi_parser.add_argument('files', nargs='+', help='Files to encrypt (supports wildcards)')
    encrypt_multi_parser.add_argument('--public-key', required=True, help='Public key file')
    encrypt_multi_parser.add_argument('--output-dir', help='Output directory for encrypted files')
    
    # Decrypt command (single file)
    decrypt_parser = subparsers.add_parser('decrypt', help='Decrypt a file')
    decrypt_parser.add_argument('file', help='.sdp file to decrypt')
    decrypt_parser.add_argument('--private-key', required=True, help='Private key file')
    decrypt_parser.add_argument('--output-dir', default='.', help='Output directory')
    
    # Decrypt-multiple command
    decrypt_multi_parser = subparsers.add_parser('decrypt-multiple', help='Decrypt multiple files')
    decrypt_multi_parser.add_argument('files', nargs='+', help='.sdp files to decrypt (supports wildcards)')
    decrypt_multi_parser.add_argument('--private-key', required=True, help='Private key file')
    decrypt_multi_parser.add_argument('--output-dir', default='.', help='Output directory')
    
    # Checker command
    check_parser = subparsers.add_parser('check', help='Check encryption status')
    check_parser.add_argument('file', nargs='?', help='File to check (optional)')
    check_parser.add_argument('--dir', default='.', help='Directory to check')
    check_parser.add_argument('--info', action='store_true', help='Show detailed info')

    # Encrypt-folder command
    encrypt_folder_parser = subparsers.add_parser('encrypt-folder', help='Encrypt all files in a folder')
    encrypt_folder_parser.add_argument('folder', help='Folder path to encrypt')
    encrypt_folder_parser.add_argument('--public-key', required=True, help='Public key file')
    encrypt_folder_parser.add_argument('--output-dir', help='Output directory for encrypted files')
    encrypt_folder_parser.add_argument('--recursive', action='store_true', help='Process subfolders recursively')
    
    # Decrypt-folder command
    decrypt_folder_parser = subparsers.add_parser('decrypt-folder', help='Decrypt all .sdp files in a folder')
    decrypt_folder_parser.add_argument('folder', help='Folder path to decrypt')
    decrypt_folder_parser.add_argument('--private-key', required=True, help='Private key file')
    decrypt_folder_parser.add_argument('--output-dir', help='Output directory for decrypted files')
    decrypt_folder_parser.add_argument('--recursive', action='store_true', help='Process subfolders recursively')

    args = parser.parse_args()
    
    if args.command == 'generate-keys':
        # Generate keys
        private_key, public_key = generate_keypair()
        
        with open(f"{args.name}_private.key", "wb") as f:
            f.write(private_key)
        with open(f"{args.name}_public.key", "wb") as f:
            f.write(public_key)
            
        print(f"✅ Keys generated: {args.name}_private.key, {args.name}_public.key")
        
    elif args.command == 'encrypt':
        # Encrypt single file
        with open(args.public_key, "rb") as f:
            pub_key = f.read()
            
        output_file = args.output or f"{args.file}.sdp"
        
        encrypt_to_sdp(pub_key, args.file, output_file)
        print(f"✅ Encrypted: {args.file} -> {output_file}")
        
    elif args.command == 'encrypt-multiple':
        # Encrypt multiple files
        encrypted_files = encrypt_multiple_files(args.public_key, args.files, args.output_dir)
        print(f"\n📊 Summary: {len(encrypted_files)} files encrypted successfully")
        
    elif args.command == 'decrypt':
        # Decrypt single file
        with open(args.private_key, "rb") as f:
            priv_key = f.read()
            
        decrypted_path = decrypt_from_sdp(priv_key, args.file, args.output_dir)
        print(f"✅ Decrypted: {args.file} -> {decrypted_path}")
        
    elif args.command == 'decrypt-multiple':
        # Decrypt multiple files
        decrypted_files = decrypt_multiple_files(args.private_key, args.files, args.output_dir)
        print(f"\n📊 Summary: {len(decrypted_files)} files decrypted successfully")
        
    elif args.command == 'check':
        # Checker functionality (tetap sama)
        if args.file:
            # Check single file
            file_path = args.file
            if os.path.exists(file_path):
                if is_sdp_encrypted(file_path):
                    print(f"✅ {file_path} - ENCRYPTED (.sdp format)")
                    
                    if args.info:
                        info = get_sdp_file_info(file_path)
                        if info:
                            print("\n📋 File Details:")
                            print(f"  Original filename: {info['filename']}")
                            print(f"  Original size: {info['original_size']:,} bytes")
                            print(f"  Encrypted size: {info['encrypted_size']:,} bytes")
                            print(f"  Algorithm: {info['algorithm']}")
                            print(f"  Timestamp: {info['timestamp']}")
                else:
                    print(f"❌ {file_path} - NOT ENCRYPTED")
            else:
                print(f"❌ File not found: {file_path}")
        else:
            # Check directory
            check_files_in_directory(args.dir)

    elif args.command == 'encrypt-folder':
        # Encrypt entire folder
        encrypted_files = encrypt_folder(args.public_key, args.folder, args.output_dir, args.recursive)
        
    elif args.command == 'decrypt-folder':
        # Decrypt entire folder
        decrypted_files = decrypt_folder(args.private_key, args.folder, args.output_dir, args.recursive)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()