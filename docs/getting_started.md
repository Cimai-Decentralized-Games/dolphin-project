# Getting Started with Dolphin

## Overview

Dolphin is a Python framework for developing Solana programs, providing a seamless experience for writing, testing, and deploying smart contracts. This guide will walk you through setting up your development environment and creating your first Dolphin program.

## Prerequisites

Before you begin, ensure you have the following installed:

```bash
# Install Rust and Cargo
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Solana CLI tools
sh -c "$(curl -sSfL https://release.solana.com/v1.17.0/install)"

# Install Anchor Framework
cargo install --git https://github.com/coral-xyz/anchor avm --locked
avm install latest
avm use latest

# Install Python 3.8 or higher
# macOS
brew install python@3.8

# Ubuntu
sudo apt-get install python3.8 python3.8-dev
```

## Installation

Install Dolphin using pip:

```bash
pip install dolphin-framework
```

## Project Initialization

Create a new Dolphin project:

```bash
# Initialize a new project
dolphin init my_program HeLLo777777777777777777777777777777777777777

# Structure created:
my_program/
├── Cargo.toml          # Rust dependencies
├── Anchor.toml         # Anchor configuration
├── src/
│   └── lib.rs         # Generated Rust program
├── program/
│   └── lib.py         # Your Python program
├── tests/
│   └── test_program.py
└── client/            # JavaScript client
    ├── package.json
    └── src/
        └── index.ts
```

## Writing Your First Program

Edit `program/lib.py`:

```python
from dolphin.prelude import *

@program("HeLLo777777777777777777777777777777777777777")
class HelloWorldProgram:
    @account
    class Counter:
        authority: Pubkey
        count: u64
        
    @instruction
    def initialize(
        self,
        counter: Counter,
        authority: Signer,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        counter.authority = authority.key
        counter.count = 0
        
    @instruction
    def increment(
        self,
        counter: Counter,
        authority: Signer
    ):
        assert counter.authority == authority.key, "Invalid authority"
        counter.count += 1
```

## Building and Testing

```bash
# Build your program
dolphin build

# Run tests
dolphin test

# Deploy to devnet
dolphin deploy --network devnet
```

## Program Structure

### Accounts

Accounts store program state:

```python
@account
class GameState:
    authority: Pubkey
    score: u64
    player_name: str
```

### Instructions

Instructions define program logic:

```python
@instruction
def update_score(
    self,
    state: GameState,
    authority: Signer,
    new_score: u64
):
    assert state.authority == authority.key, "Invalid authority"
    state.score = new_score
```

### Program Derived Addresses (PDAs)

Create deterministic addresses:

```python
@account
@pda(seeds=["player", "game"])
class PlayerState:
    player: Pubkey
    game: Pubkey
    score: u64
```

## Development Workflow

1. **Write Program**: Create your program in Python using Dolphin decorators and types.

2. **Build**: Dolphin converts your Python code to Rust:
   ```bash
   dolphin build
   ```

3. **Test**: Write and run tests:
   ```python
   from dolphin.testing import ProgramTest
   
   async def test_counter():
       program = await ProgramTest.load("program/lib.py")
       counter = await program.create_account("Counter")
       await program.initialize(counter=counter)
       assert counter.count == 0
   ```

4. **Deploy**: Deploy to Solana:
   ```bash
   dolphin deploy --network devnet
   ```

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

## Next Steps

- Explore the [API Reference](api_reference.md)
- Check out [Example Programs](../examples/)
- Join our [Discord Community](https://discord.gg/dolphin)
- Read the [Contributing Guide](../CONTRIBUTING.md)
