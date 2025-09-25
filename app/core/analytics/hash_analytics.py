import hashlib
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import magic


class HashAnalyticsEngine:
    """Engine for hash file analysis and verification"""
    
    def __init__(self):
        self.supported_algorithms = ['md5', 'sha1', 'sha256', 'sha512']
        self.known_hash_databases = {
            'malware': 'data/hash_db/malware_hashes.json',
            'clean': 'data/hash_db/clean_hashes.json',
            'suspicious': 'data/hash_db/suspicious_hashes.json'
        }
    
    def calculate_file_hash(self, file_path: str, algorithm: str = 'sha256') -> Optional[str]:
        """Calculate hash of a file"""
        if algorithm not in self.supported_algorithms:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            print(f"Error calculating hash: {e}")
            return None
    
    def calculate_multiple_hashes(self, file_path: str) -> Dict[str, str]:
        """Calculate multiple hash algorithms for a file"""
        hashes = {}
        for algorithm in self.supported_algorithms:
            hash_value = self.calculate_file_hash(file_path, algorithm)
            if hash_value:
                hashes[algorithm] = hash_value
        return hashes
    
    def verify_file_integrity(self, file_path: str, expected_hash: str, algorithm: str = 'sha256') -> Dict[str, Any]:
        """Verify file integrity against expected hash"""
        calculated_hash = self.calculate_file_hash(file_path, algorithm)
        
        if not calculated_hash:
            return {
                'verified': False,
                'error': 'Could not calculate hash',
                'expected': expected_hash,
                'calculated': None
            }
        
        is_verified = calculated_hash.lower() == expected_hash.lower()
        
        return {
            'verified': is_verified,
            'expected': expected_hash,
            'calculated': calculated_hash,
            'algorithm': algorithm,
            'verification_time': datetime.utcnow().isoformat()
        }
    
    def analyze_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Analyze file metadata and characteristics"""
        try:
            stat = os.stat(file_path)
            file_size = stat.st_size
            
            # Get MIME type
            mime_type = magic.from_file(file_path, mime=True)
            file_type = magic.from_file(file_path)
            
            # Calculate entropy (randomness measure)
            entropy = self._calculate_entropy(file_path)
            
            # Check if file is encrypted/compressed
            is_encrypted = self._is_likely_encrypted(file_path, entropy)
            is_compressed = self._is_compressed_file(file_path)
            
            return {
                'file_size': file_size,
                'mime_type': mime_type,
                'file_type': file_type,
                'entropy': entropy,
                'is_encrypted': is_encrypted,
                'is_compressed': is_compressed,
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'accessed_time': datetime.fromtimestamp(stat.st_atime).isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_entropy(self, file_path: str, chunk_size: int = 1024) -> float:
        """Calculate Shannon entropy of file"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read(chunk_size)
            
            if not data:
                return 0.0
            
            # Count byte frequencies
            byte_counts = [0] * 256
            for byte in data:
                byte_counts[byte] += 1
            
            # Calculate entropy
            entropy = 0.0
            data_len = len(data)
            
            for count in byte_counts:
                if count > 0:
                    probability = count / data_len
                    entropy -= probability * (probability.bit_length() - 1)
            
            return entropy
        except:
            return 0.0
    
    def _is_likely_encrypted(self, file_path: str, entropy: float) -> bool:
        """Check if file is likely encrypted based on entropy"""
        # High entropy (> 7.5) suggests encryption or compression
        return entropy > 7.5
    
    def _is_compressed_file(self, file_path: str) -> bool:
        """Check if file is compressed"""
        compressed_extensions = ['.zip', '.rar', '.7z', '.gz', '.bz2', '.xz']
        compressed_mimes = [
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed',
            'application/gzip',
            'application/x-bzip2',
            'application/x-xz'
        ]
        
        _, ext = os.path.splitext(file_path.lower())
        if ext in compressed_extensions:
            return True
        
        try:
            mime_type = magic.from_file(file_path, mime=True)
            return mime_type in compressed_mimes
        except:
            return False
    
    def search_hash_databases(self, hash_value: str) -> Dict[str, Any]:
        """Search hash in known databases"""
        results = {
            'hash': hash_value,
            'found_in_databases': [],
            'threat_level': 'unknown',
            'description': None,
            'first_seen': None,
            'last_seen': None
        }
        
        for db_name, db_path in self.known_hash_databases.items():
            if os.path.exists(db_path):
                try:
                    with open(db_path, 'r') as f:
                        db_data = json.load(f)
                    
                    if hash_value.lower() in db_data:
                        entry = db_data[hash_value.lower()]
                        results['found_in_databases'].append(db_name)
                        results['threat_level'] = db_name
                        results['description'] = entry.get('description', 'No description available')
                        results['first_seen'] = entry.get('first_seen')
                        results['last_seen'] = entry.get('last_seen')
                except Exception as e:
                    print(f"Error reading database {db_name}: {e}")
        
        return results
    
    def analyze_file_similarity(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Analyze similarity between multiple files"""
        if len(file_paths) < 2:
            return []
        
        similarities = []
        
        # Calculate hashes for all files
        file_hashes = {}
        for file_path in file_paths:
            hashes = self.calculate_multiple_hashes(file_path)
            file_hashes[file_path] = hashes
        
        # Compare files pairwise
        for i, file1 in enumerate(file_paths):
            for j, file2 in enumerate(file_paths[i+1:], i+1):
                similarity = self._calculate_file_similarity(
                    file_hashes[file1], 
                    file_hashes[file2]
                )
                
                similarities.append({
                    'file1': file1,
                    'file2': file2,
                    'similarity_score': similarity,
                    'is_identical': similarity == 1.0,
                    'is_similar': similarity > 0.8
                })
        
        return sorted(similarities, key=lambda x: x['similarity_score'], reverse=True)
    
    def _calculate_file_similarity(self, hashes1: Dict[str, str], hashes2: Dict[str, str]) -> float:
        """Calculate similarity between two files based on hashes"""
        if not hashes1 or not hashes2:
            return 0.0
        
        # Check for exact matches
        for algorithm in self.supported_algorithms:
            if algorithm in hashes1 and algorithm in hashes2:
                if hashes1[algorithm] == hashes2[algorithm]:
                    return 1.0
        
        # If no exact matches, return 0
        return 0.0
    
    def generate_hash_report(self, file_path: str) -> Dict[str, Any]:
        """Generate comprehensive hash analysis report"""
        # Calculate all hashes
        hashes = self.calculate_multiple_hashes(file_path)
        
        # Analyze metadata
        metadata = self.analyze_file_metadata(file_path)
        
        # Search in databases
        db_results = {}
        for algorithm, hash_value in hashes.items():
            db_results[algorithm] = self.search_hash_databases(hash_value)
        
        return {
            'file_path': file_path,
            'hashes': hashes,
            'metadata': metadata,
            'database_results': db_results,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'recommendations': self._generate_recommendations(metadata, db_results)
        }
    
    def _generate_recommendations(self, metadata: Dict[str, Any], db_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Check for high entropy
        if metadata.get('entropy', 0) > 7.5:
            recommendations.append("High entropy detected - file may be encrypted or compressed")
        
        # Check for malware matches
        for algorithm, result in db_results.items():
            if result['threat_level'] == 'malware':
                recommendations.append(f"File matches known malware hash ({algorithm})")
        
        # Check for suspicious matches
        for algorithm, result in db_results.items():
            if result['threat_level'] == 'suspicious':
                recommendations.append(f"File matches suspicious hash ({algorithm})")
        
        # Check file size
        file_size = metadata.get('file_size', 0)
        if file_size > 100 * 1024 * 1024:  # 100MB
            recommendations.append("Large file size - consider compression or archiving")
        
        if not recommendations:
            recommendations.append("No specific issues detected")
        
        return recommendations
