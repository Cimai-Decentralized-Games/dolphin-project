# Dolphin API Reference

[Previous content up to Game Development section...]

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
