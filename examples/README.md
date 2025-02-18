# Dolphin Examples

This directory contains example programs demonstrating various features of the Dolphin framework.

## Basic Examples

### 1. [Basic Counter](01_basic_program.py)
A simple counter program demonstrating basic account management and instructions.

```python
from dolphin.prelude import *

@program("CounterProg111111111111111111111111111111111111")
class CounterProgram:
    @account
    class Counter:
        authority: Pubkey
        count: u64

    @instruction
    def initialize(self, counter: Counter, authority: Signer):
        counter.authority = authority.key()
        counter.count = 0

    @instruction
    def increment(self, counter: Counter, authority: Signer):
        assert counter.authority == authority.key(), "Invalid authority"
        counter.count += 1
```

### 2. [Token Program](02_basic_program.py)
A basic token program showing token creation and transfers.

```python
@program("TokenProg111111111111111111111111111111111111")
class TokenProgram:
    @account
    class TokenMint:
        authority: Pubkey
        supply: u64
        decimals: u8

    @account
    @pda(seeds=["token", "owner"])
    class TokenAccount:
        owner: Pubkey
        mint: Pubkey
        amount: u64
```

## Advanced Examples

### 3. [NFT Marketplace](03_nft_marketplace.py)
A complete NFT marketplace with listing, bidding, and trading functionality.

Key features:
- NFT minting and metadata
- Marketplace listings
- Bidding system
- Royalty distribution

### 4. [Staking Program](04_staking_program.py)
A staking program with rewards distribution.

Features:
- Token staking
- Reward calculation
- Compound interest
- Lock periods

### 5. [Multisig Wallet](05_multisig_wallet.py)
A multi-signature wallet implementation.

Features:
- Multiple signers
- Transaction proposal
- Execution threshold
- Timelock functionality

## Game Examples

### 6. [Hello World Game](hello_world_game.py)
A simple game demonstrating Dolphin's game development features.

```python
@program("HeLLo777777777777777777777777777777777777777")
class HelloWorldGame:
    @account
    class GameState(GameState):
        player: Pubkey
        score: u64
        last_play: UnixTimestamp

    @account
    @pda(seeds=["player"])
    class PlayerState:
        owner: Pubkey
        games_played: u64
        wins: u64
```

## Running Examples

1. Build an example:
```bash
# Navigate to example directory
cd examples

# Build specific example
dolphin build hello_world_game.py
```

2. Run tests:
```bash
# Run all example tests
make test-examples

# Run specific example test
pytest tests/examples/test_hello_world_game.py
```

3. Deploy:
```bash
# Deploy to devnet
dolphin deploy hello_world_game.py --network devnet
```

## Project Structure

Each example follows this structure:

```
example_name/
├── program/
│   └── lib.py          # Main program code
├── tests/
│   └── test_program.py # Program tests
└── client/             # JavaScript client
    └── src/
        └── index.ts    # Client implementation
```

## Best Practices Demonstrated

1. **Account Management**
   - Proper account validation
   - PDA usage
   - State management

2. **Security**
   - Authority checks
   - Signer validation
   - Access control

3. **Error Handling**
   - Custom error types
   - Proper error messages
   - Validation checks

4. **Testing**
   - Unit tests
   - Integration tests
   - Error case testing

## Game Development Features

1. **State Management**
   ```python
   @account
   class GameState:
       version: u8
       authority: Pubkey
       is_initialized: bool
   ```

2. **Agent Integration**
   ```python
   from dolphin.dolphin_games import train_agent

   agent = train_agent(
       game=game,
       training_params={
           "episodes": 1000,
           "learning_rate": 0.001
       }
   )
   ```

3. **Casino Integration**
   ```python
   from dolphin.dolphin_games import deploy_to_casino

   deploy_to_casino(
       game=game,
       agent=agent,
       casino_program_id=CASINO_ID
   )
   ```

## Contributing

To add a new example:

1. Create a new file in the examples directory
2. Add corresponding tests
3. Update this README
4. Submit a pull request

Guidelines:
- Include clear documentation
- Add comprehensive tests
- Follow Dolphin best practices
- Demonstrate practical use cases

## Support

For questions about the examples:
- Join our [Discord](https://discord.gg/dolphin)
- Check the [Documentation](https://docs.dolphin.dev)
- Open an [Issue](https://github.com/yourusername/dolphin/issues)
