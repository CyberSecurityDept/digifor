from .core import SDPCrypto

generate_keypair = SDPCrypto.generate_keypair
encrypt_to_sdp = SDPCrypto.encrypt_to_sdp  
decrypt_from_sdp = SDPCrypto.decrypt_from_sdp

__all__ = ['generate_keypair', 'encrypt_to_sdp', 'decrypt_from_sdp']