```markdown
# Getting Started with Dolphin

Dolphin is a Python-to-Solana framework that allows you to write Solana programs using Python syntax or the specialized Dolphin Language (DL).

## Installation

### Prerequisites

- Python 3.7 or higher
- Rust and Cargo
- Solana CLI tools
- Anchor Framework

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Solana
sh -c "$(curl -sSfL https://release.solana.com/v1.17.0/install)"

# Install Anchor
cargo install --git https://github.com/coral-xyz/anchor avm --locked
avm install latest
avm use latest

# Install Dolphin
pip install dolphin-framework
```

## Basic Usage

### 1. Using Python Syntax

Create a new Solana program using Python decorators:

```python
from dolphin.prelude import 

@program("CounterProg111111111111111111111111111111111111")
class CounterProgram:
    @account
    class Counter:
        authority: Pubkey
        count: u64

    @instruction
    def initialize(self, authority: Pubkey):
        self.counter.authority = authority
        self.counter.count = 0

    @instruction
    def increment(self):
        assert self.counter.authority == self.signer, "Only authority can increment"
        self.counter.count += 1
```

### 2. Using Dolphin Language (DL)

Alternatively, use the more concise DL syntax:

```
program Counter {
    id: "CounterProg111111111111111111111111111111111111"
    account Counter {
        authority: pubkey
        count: u64
    }
    ix initialize(authority: pubkey) {
        @counter.authority = authority
        @counter.count = 0
    }
    ix increment() {
        require(@counter.authority == @signer, "Only authority can increment")
        @counter.count += 1
    }
}
```

### 3. Building and Deploying

```bash
# Build your program
dolphin build counter_program.py  # or counter_program.dl

# Deploy to devnet
dolphin deploy --network devnet

# Deploy to mainnet
dolphin deploy --network mainnet-beta
```

## Core Concepts

### 1. Accounts

- Use `@account` decorator or `account` keyword in DL
- Define account structure with typed fields
- Support for PDAs using `@pda` decorator

### 2. Instructions

- Use `@instruction` decorator or `ix` keyword in DL
- Define program logic
- Automatic account validation

### 3. Types

```python
# Available types
u8, u16, u32, u64     # Unsigned integers
i8, i16, i32, i64     # Signed integers
f32, f64             # Floating point (converted to fixed-point)
bool                  # Boolean
str                   # String
Pubkey              # Solana public key
List[T]             # Arrays/Vectors
Optional[T]         # Optional values
```

### 4. Account Context

```python
@instruction
def transfer(self, amount: u64):
    # Access accounts
    self.from_account.balance -= amount
    self.to_account.balance += amount
    # Access signer
    assert self.signer == self.from_account.owner
    # Access program ID
    program_id = self.program_id
```

## Examples

1.  Basic Counter Program: [examples/01\_basic\_program.py](../python/examples/01\_basic\_program.py)
2.  Token Program: [examples/02\_token\_program.py](../python/examples/02\_token\_program.py)
3.  NFT Marketplace: [examples/03\_nft\_marketplace.py](../python/examples/03\_nft\_marketplace.py)
4.  Staking Program: [examples/04\_staking\_program.py](../python/examples/04\_staking\_program.py)
5.  Multisig Wallet: [examples/05\_multisig\_wallet.py](../python/examples/05\_multisig\_wallet.py)
6.  Using DL Syntax: [examples/06\_using\_dl\_syntax.py](../python/examples/06\_using\_dl\_syntax.py)

## Best Practices

### 1. Account Structure

- Keep account data minimal
- Use appropriate types for fields
- Consider using PDAs for deterministic addresses

### 2. Security

```python
@instruction
def withdraw(self, amount: u64):
    # Always validate authority
    assert self.account.authority == self.signer
    # Check numerical operations
    assert self.account.balance >= amount
    # Update state after validation
    self.account.balance -= amount
```

### 3. Error Handling

```python
@instruction
def process(self, data: u64):
    # Use descriptive error messages
    assert data > 0, "Data must be positive"
    assert self.account.initialized, "Account not initialized"
```

### 4. Program Organization

- Group related accounts and instructions
- Use meaningful names
- Add comments for complex logic
- Consider breaking large programs into modules

## Advanced Features

### 1. Cross-Program Invocation (CPI)

```python
@instruction
def transfer_tokens(self, amount: u64):
    self.token_program.transfer(
        from_account=self.sender,
        to_account=self.receiver,
        authority=self.signer,
        amount=amount
    )
```

### 2. Program Derived Addresses (PDA)

```python
@account
@pda("owner", "mint")
class TokenAccount:
    owner: Pubkey
    mint: Pubkey
    amount: u64
```

### 3. Custom Types

```python
@dataclass
class TradeDetails:
    price: u64
    quantity: u64
    side: str  # "buy" or "sell"
```

## Debugging and Testing

### 1. Local Testing

```python
from dolphin.testing import ProgramTest

async def test_counter():
    program = await ProgramTest.load("counter_program.py")
    # Create test accounts
    counter = await program.create_account("Counter")
    authority = program.create_keypair()
    # Test instructions
    await program.initialize(authority=authority.pubkey())
    assert counter.count == 0
    await program.increment()
    assert counter.count == 1
```

### 2. Error Codes

Common error codes and their meanings:

- 6000: Invalid Authority
- 6001: Insufficient Funds
- 6002: Account Not Initialized
- 6003: Invalid Account Type

## Resources

-   [Dolphin Documentation](https://docs.dolphin.dev)
-   [Solana Documentation](https://docs.solana.com)
-   [Anchor Documentation](https://anchor-lang.com)
-   [Discord Community](https://discord.gg/dolphin)
-   [GitHub Repository](https://github.com/dolphin-dev/dolphin)

## Need Help?

*   Join our [Discord](https://discord.gg/dolphin)
*   Check our [FAQ](./faq.md)
*   Open an issue on [GitHub](https://github.com/dolphin-dev/dolphin/issues)
```

