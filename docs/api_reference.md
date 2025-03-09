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

## Casino Integration

### CasinoBridge

Main interface for integrating Casino of Life with Dolphin programs.

```python
from dolphin.dolphin_games.casino_bridge import CasinoBridge
```

#### Constructor

```python
CasinoBridge(program_id: Pubkey, game_name: str = 'Airstriker-Genesis')
```

Parameters:
- `program_id`: Solana program ID for the game
- `game_name`: Name of the game ROM to use (default: 'Airstriker-Genesis')

#### Methods

##### initialize_env
```python
def initialize_env(self, state_name: str = 'tournament', 
                  scenario_path: Optional[Path] = None) -> None
```
Initializes the game environment.
- `state_name`: Initial game state name
- `scenario_path`: Optional path to scenario JSON file

##### create_agent
```python
def create_agent(self, policy: str = 'PPO',
                action_map: Optional[Dict] = None) -> None
```
Creates a game agent with specified policy.
- `policy`: RL policy to use ('PPO', 'A2C', 'DQN')
- `action_map`: Optional custom action mapping

##### train_agent
```python
def train_agent(self, timesteps: int = 100000,
               save_interval: int = 10000,
               checkpoint_dir: Optional[Path] = None) -> Dict[str, Any]
```
Trains the agent with specified parameters.
- `timesteps`: Total training timesteps
- `save_interval`: Steps between checkpoints
- `checkpoint_dir`: Directory for saving checkpoints
- Returns: Dictionary with training results

##### close
```python
def close(self) -> None
```
Closes the environment and cleans up resources.

### CasinoGameState

Represents the game state with IR compatibility.

```python
from dolphin.core.casino_types import CasinoGameState
```

#### Fields

- `version: int` - State version
- `authority: Pubkey` - Program authority
- `is_initialized: bool` - Initialization status
- `raw_frame: bytes` - Current game frame
- `reward_data: Dict[str, Any]` - Training rewards
- `agent_state: Dict[str, Any]` - Agent state
- `metadata: Dict[str, Any]` - Game metadata

#### Methods

##### update_from_casino
```python
def update_from_casino(self, frame: bytes, rewards: Dict[str, Any]) -> None
```
Updates state from Casino environment.
- `frame`: Current game frame
- `rewards`: Current rewards

##### to_ir_dict
```python
def to_ir_dict(self) -> Dict[str, Any]
```
Converts state to IR-compatible format.
Returns:
```python
{
    'version': int,
    'authority': str,
    'is_initialized': bool,
    'frame_hash': str,
    'rewards': Dict[str, Any],
    'metadata': Dict[str, Any]
}
```

### Configuration

#### Scenario Configuration Schema
```json
{
    "name": "string",
    "metadata": {
        "version": "string",
        "type": "string",
        "difficulty": "string",
        "players": "number",
        "mode": "string"
    },
    "game_files": {
        "rom": "string",
        "state": "string",
        "metadata": "string"
    }
}
```

### Usage Examples

#### Basic Setup
```python
from dolphin.prelude import *
from dolphin.dolphin_games.casino_bridge import CasinoBridge

# Initialize bridge
bridge = CasinoBridge(
    program_id=Pubkey("Your-Program-ID"),
    game_name="Airstriker-Genesis"
)

# Setup environment
bridge.initialize_env(state_name="Level1")

try:
    # Create and train agent
    bridge.create_agent(policy='PPO')
    results = bridge.train_agent(timesteps=100000)
finally:
    bridge.close()
```

#### State Management
```python
# Update state
bridge.game_state.metadata.update({
    'score': 100,
    'level': 2
})

# Update rewards
bridge.game_state.reward_data = {
    'score': 100,
    'time_bonus': 50
}

# Get IR state
ir_state = bridge.game_state.to_ir_dict()
```

#### Custom Training Configuration
```python
# Create agent with custom action mapping
bridge.create_agent(
    policy='PPO',
    action_map={
        'BUTTON_A': 'jump',
        'BUTTON_B': 'attack'
    }
)

# Train with checkpoints
results = bridge.train_agent(
    timesteps=100000,
    save_interval=10000,
    checkpoint_dir=Path("checkpoints")
)
```

For more detailed examples and use cases, refer to the [examples directory](../examples/).
