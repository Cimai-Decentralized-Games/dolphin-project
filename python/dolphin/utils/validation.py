from typing import Optional, List, Tuple
from dolphin import validation  # Rust validation module via PyO3
ValidationError = validation.ValidationError  # Re-export error class

def validate_address(address: str) -> bool:
    """Validate a Solana address using Rust implementation"""
    return validation.validate_pubkey(address)

def validate_program_id(program_id: str) -> bool:
    """Validate a Solana program ID using Rust implementation"""
    return validation.validate_program_id(program_id)

def validate_identifier(name: str) -> bool:
    """Validate an identifier name using Rust implementation"""
    return validation.validate_identifier(name)

def validate_type_name(name: str) -> bool:
    """Validate a type name using Rust implementation"""
    return validation.validate_type_name(name)

def validate_account_name(name: str) -> bool:
    """Validate an account name using Rust implementation"""
    return validation.validate_account_name(name)

def validate_field_name(name: str) -> bool:
    """Validate a field name using Rust implementation"""
    return validation.validate_field_name(name)

def validate_instruction_name(name: str) -> bool:
    """Validate an instruction name using Rust implementation"""
    return validation.validate_instruction_name(name)

def validate_solana_type(type_name: str) -> bool:
    """Validate a Solana type using Rust implementation"""
    return validation.validate_solana_type(type_name)

def derive_program_address(seeds: List[bytes], program_id: str) -> str:
    """Create a program derived address (PDA) using Rust implementation"""
    return validation.derive_program_address(seeds, program_id)

def find_program_address(seeds: List[bytes], program_id: str) -> Tuple[str, int]:
    """Find a program derived address and bump seed using Rust implementation"""
    return validation.find_program_address(seeds, program_id)
