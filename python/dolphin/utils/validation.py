from typing import Optional, List
from dolphin.native import validation  # This imports our Rust validation module via PyO3

def validate_address(address: str) -> bool:
    """
    Validate a Solana address using the Rust implementation.
    
    Args:
        address: The address to validate
        
    Returns:
        bool: True if address is valid, False otherwise
    """
    return validation.validate_pubkey(address)

def validate_program_id(program_id: str) -> bool:
    """
    Validate a Solana program ID using the Rust implementation.
    
    Args:
        program_id: The program ID to validate
        
    Returns:
        bool: True if program ID is valid, False otherwise
    """
    return validation.validate_program_id(program_id)

def validate_token_mint(mint_address: str) -> bool:
    """
    Validate a token mint address.
    
    Args:
        mint_address: The mint address to validate
        
    Returns:
        bool: True if mint address is valid, False otherwise
    """
    return validate_address(mint_address)

def validate_identifier(name: str) -> bool:
    """
    Validate a Solana identifier using the Rust implementation.
    
    Args:
        name: The identifier to validate
        
    Returns:
        bool: True if identifier is valid, False otherwise
    """
    return validation.validate_identifier(name)

def validate_type_name(name: str) -> bool:
    """
    Validate a type name using the Rust implementation.
    
    Args:
        name: The type name to validate
        
    Returns:
        bool: True if type name is valid, False otherwise
    """
    return validation.validate_type_name(name)

def derive_program_address(seeds: List[bytes], program_id: str) -> Optional[str]:
    """
    Derive a program derived address (PDA).
    Note: This still needs to be implemented in Rust for proper PDA derivation.
    
    Args:
        seeds: List of seeds to derive the address
        program_id: The program ID
        
    Returns:
        Optional[str]: The derived address if valid, None otherwise
    """
    # TODO: Implement this in Rust and expose via PyO3
    raise NotImplementedError("PDA derivation needs to be implemented in Rust")
