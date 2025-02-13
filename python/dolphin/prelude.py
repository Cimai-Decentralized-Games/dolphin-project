"""
Dolphin Framework Prelude

This module exports commonly used types and decorators for Solana program development.
Import this module to get started with Dolphin development.
"""

from typing import List, Optional, Union, Dict, Any
from dataclasses import dataclass
from base58 import b58encode, b58decode
from . import native  # This imports our Rust functions

# Re-export core decorators
from .core.decorators import (
    program,
    account,
    instruction,
    pda,
    mutable,
    signer
)

# Re-export core types
from .core.types import (
    SolanaAccount,
    AccountDefinition,
    InstructionDefinition,
    TokenAccount
)

# Solana primitive types
class Pubkey(str):
    """Solana public key type"""
    @classmethod
    def from_bytes(cls, bytes_data: bytes) -> 'Pubkey':
        return cls(b58encode(bytes_data).decode())

    def to_bytes(self) -> bytes:
        return b58decode(self)

# Common Solana types
u8 = int
u16 = int
u32 = int
u64 = int
i8 = int
i16 = int
i32 = int
i64 = int
f32 = float
f64 = float

# Type aliases for clarity
Amount = u64
Lamports = u64
UnixTimestamp = i64
Slot = u64

# Common account types
@dataclass
class Mint:
    """Token mint account"""
    authority: Pubkey
    supply: u64
    decimals: u8
    is_initialized: bool = True
    freeze_authority: Optional[Pubkey] = None

@dataclass
class TokenAccountData:
    """Token account data"""
    mint: Pubkey
    owner: Pubkey
    amount: u64
    delegate: Optional[Pubkey] = None
    is_initialized: bool = True
    is_frozen: bool = False
    delegate_amount: u64 = 0

# Common errors
class DolphinError(Exception):
    """Base class for Dolphin errors"""
    pass

class AccountNotFoundError(DolphinError):
    """Raised when an account is not found"""
    pass

class InsufficientFundsError(DolphinError):
    """Raised when an account has insufficient funds"""
    pass

class InvalidProgramError(DolphinError):
    """Raised when a program ID is invalid"""
    pass

# Utility functions
def create_program_address(seeds: List[Union[bytes, str]], program_id: Pubkey) -> Pubkey:
    """Create a program derived address (PDA)"""
    # Convert seeds to bytes if they're strings
    seed_bytes = [
        s.encode('utf-8') if isinstance(s, str) else s
        for s in seeds
    ]
    
    # Call Rust implementation
    address = native.create_program_address(seed_bytes, str(program_id))
    return Pubkey(address)

def find_program_address(seeds: List[Union[bytes, str]], program_id: Pubkey) -> tuple[Pubkey, int]:
    """Find a program derived address and bump seed"""
    # Convert seeds to bytes if they're strings
    seed_bytes = [
        s.encode('utf-8') if isinstance(s, str) else s
        for s in seeds
    ]
    
    # Call Rust implementation
    address, bump = native.find_program_address(seed_bytes, str(program_id))
    return Pubkey(address), bump

# Common constants
SYSTEM_PROGRAM_ID = Pubkey("11111111111111111111111111111111")
TOKEN_PROGRAM_ID = Pubkey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
RENT_SYSVAR_ID = Pubkey("SysvarRent111111111111111111111111111111111")
CLOCK_SYSVAR_ID = Pubkey("SysvarC1ock11111111111111111111111111111111")

# Example usage in docstring
__doc__ += """
Example usage:

from dolphin.prelude import *

@program("MyProgFg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS")
class MyProgram:
    @account
    class UserAccount:
        owner: Pubkey
        balance: u64
        data: List[u8]

    @instruction
    def initialize(self, owner: Pubkey):
        # Implementation
        pass

    @instruction
    def transfer(self, amount: u64):
        # Implementation
        pass

Example PDA usage:

@program("MyProgFg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS")
class MyProgram:
    @account
    @pda("owner", "mint")
    class TokenAccount:
        owner: Pubkey
        mint: Pubkey
        amount: u64

    @instruction
    def initialize(self, owner: Pubkey, mint: Pubkey):
        # PDA is automatically derived
        pda, bump = find_program_address(
            [b"token", owner.to_bytes(), mint.to_bytes()],
            self.program_id
        )
        # Rest of implementation
        pass
"""

# Version information
__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
