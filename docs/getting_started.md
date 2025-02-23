# Getting Started with Dolphin

[Previous content up to Advanced Features section...]

## Advanced Features

### Error Handling

```python
from dolphin.prelude import DolphinError

class InsufficientBalanceError(DolphinError):
    code = 6000
    message = "Insufficient balance for operation"
```

### Cross-Program Invocation (CPI)

```python
@instruction
def transfer_tokens(
    self,
    source: TokenAccount,
    destination: TokenAccount,
    authority: Signer,
    amount: u64,
    token_program: Program = TOKEN_PROGRAM_ID
):
    token_program.transfer(
        source=source,
        destination=destination,
        authority=authority,
        amount=amount
    )
```

### Program Upgrades

```bash
# Build with upgrade capability
dolphin build --upgradeable

# Deploy upgrade
dolphin upgrade --program-id <PROGRAM_ID> --buffer <BUFFER_ADDRESS>
```

### Casino Integration

The Casino integration allows you to create game environments and train agents using the casino-of-life package. Here's a complete guide to getting started:

#### Installation

First, install the required packages:
```bash
pip install dolphin-framework casino-of-life
```

#### Basic Usage

1. Create your game program:
```python
from dolphin.prelude import *

@program("Your-Program-ID")
class MyGame:
    @account
    class GameState:
        authority: Pubkey
        player: Pubkey
        score: u64
        high_score: u64
        last_play: i64
        is_initialized: bool

    @instruction
    def initialize(self, state: GameState, authority: Signer):
        state.authority = authority.key()
        state.is_initialized = True
```

2. Setup the Casino bridge:
```python
from dolphin.dolphin_games.casino_bridge import CasinoBridge

# Initialize bridge
bridge = CasinoBridge(
    program_id=Pubkey("Your-Program-ID"),
    game_name="Airstriker-Genesis"
)

try:
    # Setup environment
    bridge.initialize_env(state_name="Level1")
    
    # Create and train agent
    bridge.create_agent(policy='PPO')
    results = bridge.train_agent(
        timesteps=100000,
        save_interval=10000,
        checkpoint_dir="checkpoints"
    )
finally:
    bridge.close()  # Always close when done
```

#### State Management

Handle game state through metadata and rewards:

```python
# Update game state
bridge.game_state.metadata.update({
    'score': current_score,
    'level': current_level
})

# Update training metrics
bridge.game_state.reward_data = {
    'score': current_score,
    'time_bonus': time_bonus
}

# Get IR representation
ir_state = bridge.game_state.to_ir_dict()
```

#### Environment Configuration

Create a scenario configuration (scenario.json):
```json
{
    "name": "Training Scenario",
    "metadata": {
        "difficulty": "normal",
        "players": 1,
        "mode": "training"
    },
    "game_files": {
        "rom": "Airstriker-Genesis",
        "state": "Level1",
        "metadata": "path/to/metadata.json"
    }
}
```

Use the configuration:
```python
bridge.initialize_env(
    state_name="Level1",
    scenario_path="path/to/scenario.json"
)
```

#### Best Practices

1. Always use proper cleanup:
```python
try:
    bridge = CasinoBridge(program_id)
    bridge.initialize_env()
    # Use environment...
finally:
    bridge.close()
```

2. Handle state updates correctly:
```python
# Game state goes in metadata
bridge.game_state.metadata.update({
    'score': score,
    'level': level
})

# Training metrics go in reward_data
bridge.game_state.reward_data = {
    'score': score,
    'bonus': bonus
}
```

3. Use checkpoints for long training:
```python
bridge.train_agent(
    timesteps=100000,
    save_interval=10000,
    checkpoint_dir="checkpoints"
)
```

For more details on Casino integration, see the [API Reference](api_reference.md#casino-integration).

## Next Steps

- Explore the [API Reference](api_reference.md)
- Check out [Example Programs](../examples/)
- Join our [Discord Community](https://discord.gg/dolphin)
- Read the [Contributing Guide](../CONTRIBUTING.md)
