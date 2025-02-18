#python/dolphin/core/types.py
from typing import Optional, Any, Dict, List
from dataclasses import dataclass
from enum import Enum
from ..utils.validation import validate_address

class SolanaType(Enum):
    """Mapping of Python types to Solana types."""
    U8 = "u8"
    U16 = "u16"
    U32 = "u32"
    U64 = "u64"
    I8 = "i8"
    I16 = "i16"
    I32 = "i32"
    I64 = "i64"
    BOOL = "bool"
    PUBKEY = "Pubkey"
    STRING = "String"
    BYTES = "Vec<u8>"

    @classmethod
    def from_python_type(cls, py_type: str) -> str:
        """Convert Python type hint to Solana type."""
        type_mapping = {
            "int": cls.U64.value,
            "str": cls.STRING.value,
            "bool": cls.BOOL.value,
            "Pubkey": cls.PUBKEY.value,
            "bytes": cls.BYTES.value,
        }
        return type_mapping.get(py_type, py_type)

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

    mint: Optional[str] = None  # ✅ Default to None (not every account is a mint)
    token_amount: int = 0  # ✅ Default (Starts at 0)
    decimals: int = 9  # ✅ Default (Standard for SPL Tokens)
    is_frozen: bool = False  # ✅ Default (Not frozen by default)
    delegate: Optional[str] = None  # ✅ Default (No delegate by default)

    def __post_init__(self):
        """Additional validation for token-specific fields."""
        super().__post_init__()
        if self.mint and not validate_address(self.mint):
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


@dataclass
class AccountField:
    """Represents a field in a Solana account structure."""
    name: str
    type_name: str
    attributes: List[str] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = []

    def to_ir(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": SolanaType.from_python_type(self.type_name),
            "attributes": self.attributes
        }

@dataclass
class AccountDefinition:
    """Definition for a Solana account structure."""
    name: str
    fields: List[AccountField]
    is_pda: bool = False
    seeds: List[str] = None
    discriminator: Optional[str] = None

    def __post_init__(self):
        if self.seeds is None:
            self.seeds = []

    def add_field(self, name: str, type_name: str, attributes: List[str] = None):
        field = AccountField(name, type_name, attributes)
        self.fields.append(field)

    def set_pda(self, seeds: List[str]):
        self.is_pda = True
        self.seeds = seeds

    def to_ir(self) -> Dict[str, Any]:
        return {
            "type": "account",
            "name": self.name,
            "fields": [field.to_ir() for field in self.fields],
            "is_pda": self.is_pda,
            "seeds": self.seeds,
            "discriminator": self.discriminator
        }

@dataclass
class InstructionArgument:
    """Represents an argument in a Solana instruction."""
    name: str
    type_name: str

    def to_ir(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": SolanaType.from_python_type(self.type_name)
        }

@dataclass
class InstructionAccount:
    """Represents an account used in a Solana instruction."""
    name: str
    account_type: str
    is_mutable: bool = False
    is_signer: bool = False

    def to_ir(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.account_type,
            "is_mutable": self.is_mutable,
            "is_signer": self.is_signer
        }

@dataclass
class InstructionDefinition:
    """Definition for a Solana instruction."""
    name: str
    arguments: List[InstructionArgument]
    accounts: List[InstructionAccount]
    body: List[Dict[str, Any]]

    def __post_init__(self):
        if self.arguments is None:
            self.arguments = []
        if self.accounts is None:
            self.accounts = []
        if self.body is None:
            self.body = []

    def add_argument(self, name: str, type_name: str):
        self.arguments.append(InstructionArgument(name, type_name))

    def add_account(self, name: str, account_type: str, is_mutable: bool = False, is_signer: bool = False):
        self.accounts.append(InstructionAccount(name, account_type, is_mutable, is_signer))

    def to_ir(self) -> Dict[str, Any]:
        return {
            "type": "instruction",
            "name": self.name,
            "arguments": [arg.to_ir() for arg in self.arguments],
            "accounts": [acc.to_ir() for acc in self.accounts],
            "body": self.body
        }
