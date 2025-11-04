import os
import json
import struct

def is_sdp_encrypted(file_path):
    try:
        if not os.path.exists(file_path):
            return False
            
        file_size = os.path.getsize(file_path)
        if file_size < 40:
            return False
            
        with open(file_path, 'rb') as f:
            header_len_bytes = f.read(4)
            if len(header_len_bytes) != 4:
                return False
                
            header_len = struct.unpack('>I', header_len_bytes)[0]
            
            header_json = f.read(header_len)
            if len(header_json) != header_len:
                return False
                
            try:
                header = json.loads(header_json.decode('utf-8'))
                
                required_fields = ['version', 'filename', 'ephemeral_public_key', 'salt', 'algorithm']
                if all(field in header for field in required_fields):
                    return True
                else:
                    return False
                    
            except (json.JSONDecodeError, UnicodeDecodeError):
                return False
                
    except Exception:
        return False

def check_files_in_directory(directory='.'):
    print(f"Checking encryption status in: {os.path.abspath(directory)}")
    print("=" * 60)
    
    files = os.listdir(directory)
    results = []
    
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            is_encrypted = is_sdp_encrypted(file_path)
            status = "ENCRYPTED" if is_encrypted else "NOT ENCRYPTED"
            results.append((file, status))
    
    results.sort(key=lambda x: x[1], reverse=True)
    
    for filename, status in results:
        print(f"{status:20} {filename}")
    
    encrypted_count = sum(1 for _, status in results if status == "ENCRYPTED")
    total_count = len(results)
    
    print("=" * 60)
    print(f"Summary: {encrypted_count}/{total_count} files encrypted")
    
    return results

def get_sdp_file_info(file_path):
    if not is_sdp_encrypted(file_path):
        return None
        
    try:
        with open(file_path, 'rb') as f:
            header_len = struct.unpack('>I', f.read(4))[0]
            header_json = f.read(header_len)
            header = json.loads(header_json.decode('utf-8'))
            
            file_size = os.path.getsize(file_path)
            header_size = 4 + header_len
            footer_size = 32
            
            data_size = file_size - header_size - footer_size
            
            return {
                'filename': header.get('filename', 'Unknown'),
                'original_size': header.get('file_size', 0),
                'encrypted_size': file_size,
                'algorithm': header.get('algorithm', 'Unknown'),
                'timestamp': header.get('timestamp', 'Unknown'),
                'chunk_size': header.get('chunk_size', 0),
                'total_chunks': header.get('total_chunks', 0),
                'compression_ratio': f"{(file_size / header.get('file_size', 1)):.2f}x" if header.get('file_size') else 'N/A'
            }
    except Exception as e:
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='SDP File Encryption Checker')
    parser.add_argument('file', nargs='?', help='File to check (optional)')
    parser.add_argument('--dir', default='.', help='Directory to check')
    parser.add_argument('--info', action='store_true', help='Show detailed info')
    
    args = parser.parse_args()
    
    if args.file:
        file_path = args.file
        if os.path.exists(file_path):
            if is_sdp_encrypted(file_path):
                print(f"{file_path} - ENCRYPTED (.sdp format)")
                
                if args.info:
                    info = get_sdp_file_info(file_path)
                    if info:
                        print("\nFile Details:")
                        print(f"  Original filename: {info['filename']}")
                        print(f"  Original size: {info['original_size']:,} bytes")
                        print(f"  Encrypted size: {info['encrypted_size']:,} bytes")
                        print(f"  Algorithm: {info['algorithm']}")
                        print(f"  Timestamp: {info['timestamp']}")
                        print(f"  Chunk size: {info['chunk_size']:,} bytes")
                        print(f"  Total chunks: {info['total_chunks']}")
                        print(f"  Size ratio: {info['compression_ratio']}")
            else:
                print(f"{file_path} - NOT ENCRYPTED")
        else:
            print(f"File not found: {file_path}")
    else:
        check_files_in_directory(args.dir)