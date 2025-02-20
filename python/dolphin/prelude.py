"""
Dolphin Framework Prelude

This module exports commonly used types and decorators for Solana program development.
Import this module to get started with Dolphin development.
"""

from typing import List, Optional, Union, Dict, Any, TypeVar, Generic
from dataclasses import dataclass, field
from base58 import b58encode, b58decode
from datetime import datetime

# Re-export core decorators
from .core.decorators import (
    program,
    account,
    instruction,
    pda,
    mutable,
    signer,
    validate
)

# Re-export core types
from .core.types import (
    SolanaAccount,
    AccountDefinition,
    InstructionDefinition,
    TokenAccount,
    AccountMeta,
    Program,
    Clock
)

# Type variable for generic type hints
T = TypeVar('T')

# Solana primitive types
class Pubkey(str):
    """Solana public key type with additional functionality"""
    @classmethod
    def from_bytes(cls, bytes_data: bytes) -> 'Pubkey':
        return cls(b58encode(bytes_data).decode())

    def to_bytes(self) -> bytes:
        return b58decode(self)
    
    @classmethod
    def default(cls) -> 'Pubkey':
        """Returns default pubkey (all zeros)"""
        return cls("11111111111111111111111111111111")

    def key(self) -> 'Pubkey':
        """Get the public key"""
        return self

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
bytes32 = bytes
string = str

# Type aliases for clarity
Amount = u64
Lamports = u64
UnixTimestamp = i64
Slot = u64

@dataclass
class Result(Generic[T]):
    """Result type for handling success/failure"""
    value: Optional[T] = None
    error: Optional[str] = None
    
    @property
    def is_ok(self) -> bool:
        return self.error is None
    
    @property
    def is_err(self) -> bool:
        return self.error is not None

@dataclass
class Signer:
    """Transaction signer"""
    pubkey: Pubkey
    is_writable: bool = True
    
    def key(self) -> Pubkey:
        """Get the signer's public key"""
        return self.pubkey

@dataclass
class GameState:
    """Base class for game state accounts"""
    version: u8 = 1
    authority: Pubkey = field(default_factory=Pubkey.default)
    is_initialized: bool = False
    last_update: UnixTimestamp = field(default_factory=lambda: int(datetime.now().timestamp()))

    def validate(self) -> bool:
        """Validate account state"""
        return self.is_initialized

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
    code: int = 0
    message: str = ""

    def __init__(self, message: Optional[str] = None):
        super().__init__(message or self.message)

class AccountNotFoundError(DolphinError):
    """Raised when an account is not found"""
    code = 100
    message = "Account not found"

class InsufficientFundsError(DolphinError):
    """Raised when an account has insufficient funds"""
    code = 101
    message = "Insufficient funds"

class InvalidProgramError(DolphinError):
    """Raised when a program ID is invalid"""
    code = 102
    message = "Invalid program ID"

from .utils.validation import ValidationError

# Utility functions
def create_program_address(seeds: List[Union[bytes, str]], program_id: Pubkey) -> Pubkey:
    """Create a program derived address (PDA)"""
    seed_bytes = [
        s.encode('utf-8') if isinstance(s, str) else s
        for s in seeds
    ]
    from .ir_gen import IRGenerator  # Import here to avoid circular imports
    address = IRGenerator.generate_pda(seed_bytes, str(program_id))
    return Pubkey(address)

def find_program_address(seeds: List[Union[bytes, str]], program_id: Pubkey) -> tuple[Pubkey, int]:
    """Find a program derived address and bump seed"""
    seed_bytes = [
        s.encode('utf-8') if isinstance(s, str) else s
        for s in seeds
    ]
    from .ir_gen import IRGenerator  # Import here to avoid circular imports
    address, bump = IRGenerator.find_pda(seed_bytes, str(program_id))
    return Pubkey(address), bump

# Common constants
SYSTEM_PROGRAM_ID = Pubkey("11111111111111111111111111111111")
TOKEN_PROGRAM_ID = Pubkey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
RENT_SYSVAR_ID = Pubkey("SysvarRent111111111111111111111111111111111")
CLOCK_SYSVAR_ID = Pubkey("SysvarC1ock11111111111111111111111111111111")
METADATA_PROGRAM_ID = Pubkey("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")

# Version information
__version__ = "0.1.0"
__author__ = "Your_name_here"
__email__ = "Your_email_@awesome_email"

# Example usage in docstring
__doc__ += """
Example usage:

from dolphin.prelude import *

@program("MyProgFg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS")
class MyProgram:
    @account
    class GameAccount(GameState):
        player: Pubkey
        score: u64
        last_play: UnixTimestamp

    @instruction
    def initialize(
        self,
        game: GameAccount,
        authority: Signer,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        game.authority = authority.key()
        game.score = 0
        game.last_play = 0
        game.is_initialized = True

    @instruction
    def play(
        self,
        game: GameAccount,
        player: Signer,
        clock: Clock = CLOCK_SYSVAR_ID
    ):
        assert game.authority == player.key(), "Invalid player"
        assert game.is_initialized, "Game not initialized"
        game.score += 1
        game.last_play = clock.unix_timestamp

Example PDA usage:

@program("MyProgFg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS")
class GameProgram:
    @account
    @pda(seeds=["game", "player"])
    class PlayerState(GameState):
        player: Pubkey
        score: u64
        level: u8

    @instruction
    def initialize_player(
        self,
        state: PlayerState,
        player: Signer,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        state.authority = player.key()
        state.player = player.key()
        state.score = 0
        state.level = 1
        state.is_initialized = True
"""
