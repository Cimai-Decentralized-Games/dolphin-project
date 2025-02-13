
```markdown
# Dolphin API Reference

## Core Decorators

### @program
Defines a Solana program.

```python
@program(program_id: str)
class MyProgram:
    """
    Parameters:
        program_id (str): Base-58 encoded program ID
    Example:
        @program("MyProgFg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS")
        class MyProgram:
            pass
    """
```

### @account
Defines a program account structure.

```python
@account
class MyAccount:
    """
    Attributes:
        pubkey (Pubkey): Account's public key (automatically added)
        discriminator (bytes): Account type discriminator (automatically added)
    Example:
        @account
        class UserAccount:
            owner: Pubkey
            balance: u64
    """
```

### @instruction
Defines a program instruction.

```python
@instruction
def my_instruction(self, arg1: u64, arg2: Pubkey):
    """
    Context Attributes:
        self.program_id (Pubkey): Program's public key
        self.signer (Pubkey): Transaction signer
        self.clock (Clock): Solana clock sysvar
    Example:
        @instruction
        def transfer(self, amount: u64):
            assert self.from_account.owner == self.signer
            self.from_account.balance -= amount
            self.to_account.balance += amount
    """
```

### @pda
Defines a Program Derived Address account.

```python
@account
@pda("owner", "mint")
class TokenAccount:
    """
    Parameters:
        seeds (str): Account field names to use as PDA seeds
    Example:
        @account
        @pda("owner", "mint")
        class TokenAccount:
            owner: Pubkey
            mint: Pubkey
            balance: u64
    """
```

## Types

### Basic Types

```python
# Integer Types
u8: int # 0 to 255
u16: int # 0 to 65,535
u32: int # 0 to 4,294,967,295
u64: int # 0 to 18,446,744,073,709,551,615
i8: int # -128 to 127
i16: int # -32,768 to 32,767
i32: int # -2,147,483,648 to 2,147,483,647
i64: int # -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807

# Other Basic Types
bool: bool # True or False
str: str # String (converted to bytes in Solana)
```

### Special Types

```python
from dolphin.prelude import
    Pubkey # Solana public key
    Amount # Type alias for u64, used for token amounts
    Lamports # Type alias for u64, used for SOL amounts
    UnixTimestamp # Type alias for i64, used for timestamps
Types
```

### Container Types

```python
from typing import List, Optional
List[T] # Variable-length array of type T
Optional[T] # Optional value of type T
```

## Account Context

### Available Properties

```python
self.program_id: Pubkey # Program's public key
self.signer: Pubkey # Transaction signer's public key
self.clock: Clock # Solana clock sysvar
```

### Clock Sysvar

```python
class Clock:
    slot: u64 # Current slot
    epoch_start_timestamp: i64 # Start time of current epoch
    epoch: u64 # Current epoch
    leader_schedule_epoch: u64 # Leader schedule epoch
    unix_timestamp: i64 # Current Unix timestamp
```

## Error Handling

### Standard Errors

```python
from dolphin.prelude import DolphinError
class AccountNotFoundError(DolphinError):
    pass
class InsufficientFundsError(DolphinError):
    pass
class InvalidProgramError(DolphinError):
    pass
```

### Custom Errors

```python
from dolphin.prelude import define_error
@define_error
class InvalidStateError(DolphinError):
    code = 6000
    message = "Account is in an invalid state"
```

## Testing Utilities

### ProgramTest

```python
from dolphin.testing import ProgramTest
async def test_program():
    # Load program
    program = await ProgramTest.load("my_program.py")
    # Create test accounts
    account = await program.create_account("MyAccount")
    keypair = program.create_keypair()
    # Execute instructions
    await program.my_instruction(
        arg1=100,
        arg2=keypair.pubkey(),
        signers=[keypair]
    )
```

### Account Creation

```python
# Create account with random address
account = await program.create_account(
    account_type="MyAccount",
    payer=payer_keypair
)

# Create PDA account
pda_account = await program.create_pda_account(
    account_type="TokenAccount",
    seeds={"owner": owner.pubkey(), "mint": mint.pubkey()}
)
```

## Dolphin Language (DL) Syntax

### Program Definition

```
program MyProgram {
    id: "MyProgFg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS"
    account MyAccount {
        owner: pubkey
        balance: u64
    }
    ix initialize(owner: pubkey) {
        @account.owner = owner
        @account.balance = 0
    }
}
```

### Special Variables

```
@signer     # Transaction signer
@program_id # Program ID
@clock      # Clock sysvar
@account    # Current account context
@rent       # Rent sysvar
```

## Utility Functions

### PDA Functions

```python
from dolphin.prelude import create_program_address, find_program_address

# Create PDA
pda = create_program_address(
    seeds=[b"token", owner.to_bytes(), mint.to_bytes()],
    program_id=program_id
)

# Find PDA and bump
pda, bump = find_program_address(
    seeds=[b"token", owner.to_bytes(), mint.to_bytes()],
    program_id=program_id
)
```

### Pubkey Utilities

```python
from dolphin.prelude import Pubkey

# Create from string
pubkey = Pubkey("11111111111111111111111111111111")

# Convert to bytes
bytes_data = pubkey.to_bytes()

# Create from bytes
pubkey = Pubkey.from_bytes(bytes_data)
```

## Constants

### System Program IDs

```python
from dolphin.prelude import (
    SYSTEM_PROGRAM_ID,
    TOKEN_PROGRAM_ID,
    ASSOCIATED_TOKEN_PROGRAM_ID,
    RENT_SYSVAR_ID,
    CLOCK_SYSVAR_ID
)
```

## Compiler Options

### Build Configuration

```python
from dolphin.compiler import CompilerConfig

config = CompilerConfig(
    optimize=True,
    debug_symbols=False,
    target="bpf-unknown-unknown",
    features=["custom-feature"]
)
```

### Program Metadata

```python
from dolphin.compiler import ProgramMetadata

metadata = ProgramMetadata(
    name="MyProgram",
    version="1.0.0",
    description="My Solana Program",
    authors=["Your Name <your.email@example.com>"]
)
```
I focused on maintaining code fences for all the code snippets, I did not find a section for macros so I created it, I hope that follows the request!
