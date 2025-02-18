# Dolphin API Reference

## Core Modules

### dolphin.prelude

The main module for Dolphin development, providing all essential types and decorators.

```python
from dolphin.prelude import *
```

### dolphin.testing

Testing utilities for Dolphin programs.

```python
from dolphin.testing import ProgramTest, create_account
```

## Decorators

### @program

Defines a Solana program.

```python
@program(program_id: str)
class MyProgram:
    """
    Args:
        program_id: Base-58 encoded program ID
    """
```

### @account

Defines a program account.

```python
@account
class GameState:
    """
    Attributes:
        authority: Pubkey
        score: u64
    """
    authority: Pubkey
    score: u64
```

### @instruction

Defines a program instruction.

```python
@instruction
def initialize(
    self,
    state: GameState,
    authority: Signer,
    system_program: Program = SYSTEM_PROGRAM_ID
):
    """
    Args:
        state: Account to initialize
        authority: Signer of the transaction
        system_program: System program for rent
    """
```

### @pda

Creates a Program Derived Address account.

```python
@account
@pda(seeds=["player", "game"])
class PlayerState:
    """
    Args:
        seeds: List of field names to use as PDA seeds
    """
    player: Pubkey
    game: Pubkey
    score: u64
```

## Types

### Basic Types

```python
# Integer Types
u8: int      # 0 to 255
u16: int     # 0 to 65,535
u32: int     # 0 to 4,294,967,295
u64: int     # 0 to 18,446,744,073,709,551,615
i8: int      # -128 to 127
i16: int     # -32,768 to 32,767
i32: int     # -2,147,483,648 to 2,147,483,647
i64: int     # -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807

# Other Types
bool: bool   # True or False
str: str     # String (stored as bytes)
bytes: bytes # Raw bytes
```

### Special Types

```python
# Account Types
Pubkey       # Solana public key
Signer       # Transaction signer
Program      # Program account

# Amount Types
Amount       # Token amount (u64)
Lamports     # SOL amount (u64)

# Time Types
UnixTimestamp # Unix timestamp (i64)
Slot         # Slot number (u64)
```

### Account Types

```python
@dataclass
class Mint:
    """Token mint account"""
    authority: Pubkey
    supply: u64
    decimals: u8
    freeze_authority: Optional[Pubkey] = None

@dataclass
class TokenAccount:
    """Token account"""
    mint: Pubkey
    owner: Pubkey
    amount: u64
    delegate: Optional[Pubkey] = None
```

## Constants

```python
# System Program IDs
SYSTEM_PROGRAM_ID: Pubkey
TOKEN_PROGRAM_ID: Pubkey
ASSOCIATED_TOKEN_PROGRAM_ID: Pubkey

# Sysvar Accounts
RENT_SYSVAR_ID: Pubkey
CLOCK_SYSVAR_ID: Pubkey
```

## Error Handling

### Built-in Errors

```python
class DolphinError(Exception):
    """Base class for Dolphin errors"""
    pass

class AccountNotFoundError(DolphinError):
    """Account not found"""
    pass

class InsufficientFundsError(DolphinError):
    """Insufficient funds"""
    pass
```

### Custom Errors

```python
class GameError(DolphinError):
    """Custom game error"""
    code = 6000
    message = "Game error occurred"
```

## Testing

### ProgramTest

```python
from dolphin.testing import ProgramTest

async def test_program():
    # Load program
    program = await ProgramTest.load("program/lib.py")
    
    # Create test accounts
    game = await program.create_account("GameState")
    player = program.create_keypair()
    
    # Execute instructions
    await program.initialize(
        state=game,
        authority=player
    )
    
    # Verify state
    assert game.score == 0
```

### Account Creation

```python
# Create regular account
account = await program.create_account(
    "GameState",
    payer=payer
)

# Create PDA account
pda = await program.create_pda(
    "PlayerState",
    seeds={
        "player": player.pubkey(),
        "game": game.pubkey()
    }
)
```

## CLI Commands

```bash
# Initialize new project
dolphin init <name> <program_id>

# Build program
dolphin build

# Run tests
dolphin test

# Deploy program
dolphin deploy --network devnet

# Upgrade program
dolphin upgrade --program-id <id> --buffer <addr>
```

## Development Tools

### IR Generation

```python
from dolphin.ir_gen import IRGenerator

# Generate IR from source
generator = IRGenerator(source_code)
ir = generator.generate()

# Convert to JSON
ir_json = ir.to_json()
```

### Validation

```python
from dolphin.utils.validation import (
    validate_pubkey,
    validate_program_id,
    validate_identifier
)

# Validate inputs
assert validate_pubkey(pubkey)
assert validate_program_id(program_id)
assert validate_identifier(name)
```

## Game Development

### Game Program

```python
from dolphin.dolphin_games import GameProgram, GameAgent

# Create game
game = GameProgram(
    name="My Game",
    program_id=program_id,
    metadata=metadata
)

# Train agent
agent = train_agent(
    game=game,
    training_params={
        "episodes": 1000,
        "learning_rate": 0.001
    }
)

# Deploy to casino
deploy_to_casino(game, agent, casino_id)
```

### Game State

```python
@account
class GameState:
    version: u8
    authority: Pubkey
    is_initialized: bool = True
    
    def validate(self) -> bool:
        return self.is_initialized
```

For more detailed examples and use cases, refer to the [examples directory](../examples/).
