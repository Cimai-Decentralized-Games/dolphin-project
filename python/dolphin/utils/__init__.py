"""Dolphin utility functions"""
from .validation import (
    validate_address,
    validate_program_id,
    validate_identifier,
    validate_type_name,
    derive_program_address
)

# Import Rust validation functions
try:
    from dolphin import (
        validate_pubkey,
        validate_program_id as _rust_validate_program_id,
        validate_identifier as _rust_validate_identifier,
        validate_type_name as _rust_validate_type_name
    )
    # Override Python implementations with Rust ones
    validate_address = validate_pubkey
    validate_program_id = _rust_validate_program_id
    validate_identifier = _rust_validate_identifier
    validate_type_name = _rust_validate_type_name
except ImportError:
    # Fall back to Python implementations if Rust extensions aren't available
    pass

__all__ = [
    'validate_address',
    'validate_program_id',
    'validate_identifier',
    'validate_type_name',
    'derive_program_address',
]