import pytest
import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from dolphin.ir_gen import IRGenerator
from dolphin import DolphinCompiler
from dolphin.core.types import SolanaType

# Constants for test configuration
TEST_DIR = Path(__file__).parent
TEST_PROGRAMS_DIR = TEST_DIR / "test_programs"
TEST_OUTPUT_DIR = TEST_DIR / "test_output"
EXAMPLE_PROGRAM_ID = "Test999999999999999999999999999999999999999"
SOLANA_NETWORK = "devnet"  # Use devnet by default
SOLANA_RPC_URL = "https://api.devnet.solana.com"

@pytest.fixture(scope="session")
def event_loop():
    """Create and provide an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_dirs():
    """Create and cleanup test directories."""
    TEST_PROGRAMS_DIR.mkdir(exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)
    
    yield TEST_PROGRAMS_DIR, TEST_OUTPUT_DIR
    
    # Cleanup after tests
    shutil.rmtree(TEST_OUTPUT_DIR)
    if TEST_PROGRAMS_DIR.exists():
        shutil.rmtree(TEST_PROGRAMS_DIR)

@pytest.fixture
def example_program_py():
    """Provide example Python program content."""
    return f"""
from dolphin.prelude import *

@program("{EXAMPLE_PROGRAM_ID}")
class ExampleProgram:
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
        assert self.counter.authority == self.signer
        self.counter.count += 1
"""

@pytest.fixture
def ir_generator(example_program_py):
    """Create IRGenerator instance with example program."""
    return IRGenerator(example_program_py)

@pytest.fixture(scope="session")
def solana_config():
    """Configure Solana CLI to use devnet."""
    # Set Solana config to use devnet
    subprocess.run(
        ["solana", "config", "set", "--url", SOLANA_RPC_URL],
        check=True,
        capture_output=True
    )
    
    # Verify connection
    try:
        result = subprocess.run(
            ["solana", "cluster-version"],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Connected to Solana {SOLANA_NETWORK}, version: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Could not connect to Solana {SOLANA_NETWORK}: {e.stderr}")

@pytest.fixture(scope="session")
def funded_keypair(solana_config):
    """Create and fund a test keypair on devnet."""
    # Generate new keypair
    keypair_path = TEST_DIR / "test-keypair.json"
    subprocess.run(
        ["solana-keygen", "new", "--no-bip39-passphrase", "-o", str(keypair_path)],
        check=True,
        capture_output=True
    )
    
    # Get public key
    pubkey = subprocess.run(
        ["solana-keygen", "pubkey", str(keypair_path)],
        check=True,
        capture_output=True,
        text=True
    ).stdout.strip()
    
    # Request airdrop
    try:
        subprocess.run(
            ["solana", "airdrop", "2", pubkey, "--url", SOLANA_RPC_URL],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Failed to get airdrop on {SOLANA_NETWORK}: {e.stderr}")
    
    yield {"path": str(keypair_path), "pubkey": pubkey}
    
    # Cleanup
    if keypair_path.exists():
        keypair_path.unlink()

# Custom markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "requires_network: mark test as requiring Solana network connection"
    )

@pytest.fixture(autouse=True)
def check_test_requirements(request):
    """Check test requirements based on markers."""
    # Skip network check for IR generation tests
    if "test_ir_gen" in str(request.node.fspath):
        return
        
    # For tests that need network connection
    if request.node.get_closest_marker('requires_network'):
        try:
            subprocess.run(
                ["solana", "cluster-version", "--url", SOLANA_RPC_URL],
                check=True,
                capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip(f"Could not connect to Solana {SOLANA_NETWORK}")
