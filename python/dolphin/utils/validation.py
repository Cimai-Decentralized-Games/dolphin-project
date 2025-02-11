import re
from typing import Optional
from base58 import b58decode, b58encode

def validate_address(address: str) -> bool:
    """
    Validate a Solana address.
    
    Args:
        address: The address to validate
        
    Returns:
        bool: True if address is valid, False otherwise
    """
    if not isinstance(address, str):
        return False
        
    # Check length (32-44 characters for base58 encoded public key)
    if len(address) < 32 or len(address) > 44:
        return False
        
    # Verify base58 character set
    if not re.match(r'^[1-9A-HJ-NP-Za-km-z]+$', address):
        return False
        
    try:
        # Attempt to decode base58
        decoded = b58decode(address)
        # Valid Solana addresses are 32 bytes
        return len(decoded) == 32
    except Exception:
        return False

def validate_program_id(program_id: str) -> bool:
    """
    Validate a Solana program ID.
    
    Args:
        program_id: The program ID to validate
        
    Returns:
        bool: True if program ID is valid, False otherwise
    """
    return validate_address(program_id)

def validate_token_mint(mint_address: str) -> bool:
    """
    Validate a token mint address.
    
    Args:
        mint_address: The mint address to validate
        
    Returns:
        bool: True if mint address is valid, False otherwise
    """
    return validate_address(mint_address)

def derive_program_address(seeds: list, program_id: str) -> Optional[str]:
    """
    Derive a program derived address (PDA).
    
    Args:
        seeds: List of seeds to derive the address
        program_id: The program ID
        
    Returns:
        Optional[str]: The derived address if valid, None otherwise
    """
    if not validate_program_id(program_id):
        return None
        
    try:
        # This is a simplified version - actual PDA derivation 
        # would need to match Solana's exact algorithm
        combined = b''.join([
            seed.encode() if isinstance(seed, str) else seed
            for seed in seeds
        ])
        combined += b58decode(program_id)
        return b58encode(combined[:32]).decode()
    except Exception:
        return None
