from typing import Optional, Any, Dict, List
from dataclasses import dataclass
from enum import Enum
from ..utils.validation import validate_address
from dolphin import validation
ValidationError = validation.ValidationError

from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

class Pubkey:
    """Represents a Solana public key."""
    def __init__(self, address: str):
        # Temporarily accept casino addresses while we fix validation
        if address.startswith('Casino'):
            self._address = address
        else:
            if not validate_address(address):
                raise ValueError(f"Invalid public key: {address}")
            self._address = address

    def __str__(self) -> str:
        return self._address

    def __repr__(self) -> str:
        return f"Pubkey({self._address})"

    def __eq__(self, other) -> bool:
        if isinstance(other, Pubkey):
            return self._address == other._address
        return False

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Any,
    ) -> CoreSchema:
        """Define how Pydantic should handle the Pubkey class."""
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(cls),
                core_schema.no_info_plain_validator_function(
                    lambda x: cls(x) if isinstance(x, str) else x
                )
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            )
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: CoreSchema,
        _handler: Any,
    ) -> JsonSchemaValue:
        """Define the JSON schema for the Pubkey class."""
        return {
            'type': 'string',
            'description': 'Solana public key',
            'pattern': '^[1-9A-HJ-NP-Za-km-z]{32,44}$'
        }

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
            raise ValidationError(f"Invalid account address: {self.address}")
        if not validate_address(self.owner):
            raise ValidationError(f"Invalid owner address: {self.owner}")
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
            raise ValidationError(f"Invalid mint address: {self.mint}")
        if self.delegate and not validate_address(self.delegate):
            raise ValidationError(f"Invalid delegate address: {self.delegate}")
        if self.decimals < 0 or self.decimals > 9:
            raise ValidationError("Decimals must be between 0 and 9")
        if self.token_amount < 0:
            raise ValidationError("Token amount cannot be negative")

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

@dataclass
class Clock:
    """
    Represents Solana's Clock sysvar which provides timing information to programs.
    Contains various timing-related fields used by the Solana runtime.
    """
    slot: int  # Current slot
    epoch_start_timestamp: int  # Timestamp of the current epoch's start
    epoch: int  # Current epoch
    leader_schedule_epoch: int  # The epoch for which the leader schedule has been generated
    unix_timestamp: int  # Current Unix timestamp (seconds since epoch)
    
    @classmethod
    def default(cls) -> 'Clock':
        """Create a default Clock instance with zero values."""
        return cls(
            slot=0,
            epoch_start_timestamp=0,
            epoch=0,
            leader_schedule_epoch=0,
            unix_timestamp=0
        )
    
    def to_ir(self) -> Dict[str, Any]:
        """Convert to intermediate representation."""
        return {
            "type": "sysvar",
            "name": "Clock",
            "fields": {
                "slot": self.slot,
                "epoch_start_timestamp": self.epoch_start_timestamp,
                "epoch": self.epoch,
                "leader_schedule_epoch": self.leader_schedule_epoch,
                "unix_timestamp": self.unix_timestamp
            }
        }

@dataclass
class Program(SolanaAccount):
    """
    Represents a Solana program account.
    A program account contains executable code and has the executable flag set to True.
    """
    def __init__(self, program_id: str):
        super().__init__(
            address=program_id,
            owner="BPFLoaderUpgradeab1e11111111111111111111111",
            lamports=0,
            data=b'',
            executable=True
        )
        
    @property
    def program_id(self) -> str:
        """Get the program ID (same as address)."""
        return self.address
        
    def __str__(self) -> str:
        return f"Program({self.program_id})"

@dataclass
class AccountMeta:
    """
    Represents metadata for an account used in a Solana instruction.
    Contains the account's public key and flags for whether it's writable and a signer.
    """
    pubkey: Pubkey
    is_writable: bool = False
    is_signer: bool = False

    def __eq__(self, other) -> bool:
        if not isinstance(other, AccountMeta):
            return False
        return (self.pubkey == other.pubkey and
                self.is_writable == other.is_writable and
                self.is_signer == other.is_signer)

    def __str__(self) -> str:
        flags = []
        if self.is_writable:
            flags.append("writable")
        if self.is_signer:
            flags.append("signer")
        flag_str = ", ".join(flags) if flags else "readonly"
        return f"AccountMeta({self.pubkey}, {flag_str})"

@dataclass
class GameState:
    """Represents the state of a Casino of Life game."""
    game_id: str
    agent_id: str
    version: int = 1
    is_initialized: bool = False
    raw_frame: bytes = b''
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
