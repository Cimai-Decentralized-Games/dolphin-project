from typing import Optional, Any, Dict
from dataclasses import dataclass
from ..utils.validation import validate_address

@dataclass
class SolanaAccount:
    """Base class for Solana accounts with fundamental attributes and validations."""
    
    address: str
    owner: str
    lamports: int
    data: bytes
    executable: bool = False
    rent_epoch: int = 0
    
    def __post_init__(self):
        """Validate account attributes after initialization."""
        if not validate_address(self.address):
            raise ValueError(f"Invalid account address: {self.address}")
        if not validate_address(self.owner):
            raise ValueError(f"Invalid owner address: {self.owner}")
        if self.lamports < 0:
            raise ValueError("Lamports cannot be negative")

    @property
    def is_writable(self) -> bool:
        """Check if the account is writable."""
        return not self.executable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert account to dictionary representation."""
        return {
            "address": self.address,
            "owner": self.owner,
            "lamports": self.lamports,
            "data": self.data.hex() if self.data else None,
            "executable": self.executable,
            "rent_epoch": self.rent_epoch
        }

@dataclass
class TokenAccount(SolanaAccount):
    """Specialized account class for SPL Tokens."""
    
    mint: str
    token_amount: int
    decimals: int
    is_frozen: bool = False
    delegate: Optional[str] = None
    
    def __post_init__(self):
        """Additional validation for token-specific fields."""
        super().__post_init__()
        if not validate_address(self.mint):
            raise ValueError(f"Invalid mint address: {self.mint}")
        if self.delegate and not validate_address(self.delegate):
            raise ValueError(f"Invalid delegate address: {self.delegate}")
        if self.decimals < 0 or self.decimals > 9:
            raise ValueError("Decimals must be between 0 and 9")
        if self.token_amount < 0:
            raise ValueError("Token amount cannot be negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert token account to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            "mint": self.mint,
            "token_amount": self.token_amount,
            "decimals": self.decimals,
            "is_frozen": self.is_frozen,
            "delegate": self.delegate
        })
        return base_dict
