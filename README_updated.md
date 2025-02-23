# 🐬 Dolphin Framework

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/dolphin-framework.svg)](https://pypi.org/project/dolphin-framework/)
[![PyPI version](https://badge.fury.io/py/dolphin-framework.svg)](https://badge.fury.io/py/dolphin-framework)

Dolphin is a Python framework for developing Solana smart contracts and games, offering a seamless developer experience with Python's simplicity and Solana's performance.

## ✨ Features

- 🐍 Write Solana programs in Python
- 🎮 Built-in game development support
- 🎰 Casino integration for game agents
- 🚀 Automatic compilation to Solana BPF
- 🔒 Type-safe account management
- 🔄 Built-in PDA support
- 🛠️ Comprehensive testing utilities
- 📦 Seamless deployment tools

## 🎮 Casino Integration

To integrate the Casino of Life package with Dolphin, you can use the `CasinoBridge` class provided in the `casino_bridge.py` module. This allows you to create retro game environments and train agents seamlessly.

### Example Usage

```python
from dolphin.dolphin_games.casino_bridge import CasinoBridge

def main():
    bridge = CasinoBridge(game_name='MortalKombatII-Genesis')
    bridge.train_agent(timesteps=100000)
    print("Agent trained successfully!")

if __name__ == "__main__":
    main()
```

### Installation

Make sure to install the Casino of Life package:

```bash
pip install casino-of-life
```

## 🚀 Quick Start

### Installation

```bash
# Install development tools
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
sh -c "$(curl -sSfL https://release.solana.com/v1.17.0/install)"
cargo install --git https://github.com/coral-xyz/anchor avm --locked
avm install latest
avm use latest

# Install Dolphin
pip install dolphin-framework
```

### Create Your First Program

```python
from dolphin.prelude import *

@program("HeLLo777777777777777777777777777777777777777")
class HelloWorldGame:
    @account
    class GameState(GameState):
        player: Pubkey
        score: u64
        last_play: UnixTimestamp

    @instruction
    def initialize(
        self,
        state: GameState,
        authority: Signer,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        state.authority = authority.key()
        state.is_initialized = True
        state.score = 0

    @instruction
    def play(
        self,
        state: GameState,
        player: Signer,
        clock: Clock = CLOCK_SYSVAR_ID
    ):
        assert state.authority == player.key(), "Invalid player"
        state.score += 1
        state.last_play = clock.unix_timestamp
```

### Build and Deploy

```bash
# Initialize new project
dolphin init hello_world HeLLo777777777777777777777777777777777777777

# Build program
dolphin build

# Deploy to devnet
dolphin deploy --network devnet
```

## 📚 Documentation

- [Getting Started](docs/getting_started.md)
- [API Reference](docs/api_reference.md)
- [Example Programs](examples/README.md)

## 🎮 Game Development

Dolphin provides built-in support for game development:

1. **Game State Management**
   ```python
   @account
   class GameState:
       version: u8
       authority: Pubkey
       is_initialized: bool
   ```

2. **Agent Training**
   ```python
   agent = train_agent(
       game=game,
       training_params={
           "model_type": "dqn",
           "hidden_layers": [64, 64]
       }
   )
   ```

3. **Casino Integration**
   ```python
   deploy_to_casino(
       game=game,
       agent=agent,
       casino_program_id=CASINO_ID
   )
   ```

## 🌟 Examples

1. [Basic Counter](examples/01_basic_program.py)
2. [Token Program](examples/02_basic_program.py)
3. [NFT Marketplace](examples/03_nft_marketplace.py)
4. [Staking Program](examples/04_staking_program.py)
5. [Multisig Wallet](examples/05_multisig_wallet.py)
6. [Hello World Game](examples/hello_world_game.py)

## 🛠️ Development

```bash
# Clone repository
git clone https://github.com/yourusername/dolphin.git
cd dolphin

# Setup development environment
make init-dev

# Run tests
make test
make test-integration

# Format code
make format

# Build documentation
make docs
```

## 📊 Project Status

Dolphin is currently in alpha. While it's stable enough for development and testing, we recommend thorough testing before using it in production.

## 🗺️ Roadmap

- [ ] Enhanced IDE support
- [ ] Advanced game development features
- [ ] Expanded agent training capabilities
- [ ] Casino integration improvements
- [ ] Cross-program invocation helpers
- [ ] Program composition tools

## 🔐 Security

Please report security vulnerabilities to security@dolphin.dev.
