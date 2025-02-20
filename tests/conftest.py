# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

import pytest
import asyncio
import os
import shutil
import subprocess
import tempfile
import time
from typing import Dict, Optional
from pathlib import Path
from dolphin.ir_gen import IRGenerator
from dolphin import DolphinCompiler
from dolphin.core.types import SolanaType
from dolphin.cli import DolphinCLI

# Constants for test configuration
TEST_DIR = Path(__file__).parent
TEST_PROGRAMS_DIR = TEST_DIR / "test_programs"
TEST_OUTPUT_DIR = TEST_DIR / "test_output"
EXAMPLE_PROGRAM_ID = "Test999999999999999999999999999999999999999"
SOLANA_NETWORK = "localnet"  # Use localnet for tests
SOLANA_RPC_URL = "http://localhost:8899"

def ensure_test_validator():
    """Ensure test validator is running and funded"""
    try:
        # Check if validator is running
        subprocess.run(
            ["solana", "cluster-version", "--url", SOLANA_RPC_URL],
            check=True, capture_output=True
        )
    except subprocess.CalledProcessError:
        print("\n🚀 Starting local test validator...")
        # Start validator in background
        subprocess.Popen(
            ["solana-test-validator", "--reset"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Wait for validator to start
        for _ in range(10):
            try:
                subprocess.run(
                    ["solana", "cluster-version", "--url", SOLANA_RPC_URL],
                    check=True, capture_output=True
                )
                print("✨ Test validator running")
                return
            except subprocess.CalledProcessError:
                time.sleep(1)
        raise RuntimeError("Failed to start test validator")

# Project initialization test constants
INIT_TEST_DIR = TEST_DIR / "init_test"
TEST_PROJECT_NAME = "test_program"
TEST_PROGRAM_ID = "Test111111111111111111111111111111111111111"

@pytest.fixture(scope="function")
def temp_test_dir():
    """Create a temporary directory for testing project initialization"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        yield temp_path

@pytest.fixture
def init_test_context(temp_test_dir):
    """Setup context for testing project initialization"""
    project_dir = temp_test_dir / TEST_PROJECT_NAME
    
    yield {
        "base_dir": temp_test_dir,
        "project_dir": project_dir,
        "program_id": TEST_PROGRAM_ID
    }
    
    # Cleanup
    if project_dir.exists():
        shutil.rmtree(project_dir)

def verify_project_structure(project_dir: Path):
    """Helper to verify the created project structure"""
    # Check root level files
    assert (project_dir / "Cargo.toml").exists(), "Cargo.toml not found"
    assert (project_dir / "Anchor.toml").exists(), "Anchor.toml not found"
    
    # Check directories
    assert (project_dir / "src").exists(), "src directory not found"
    assert (project_dir / "program").exists(), "program directory not found"
    assert (project_dir / "tests").exists(), "tests directory not found"
    assert (project_dir / "client").exists(), "client directory not found"
    
    # Check key files
    assert (project_dir / "src" / "lib.rs").exists(), "lib.rs not found"
    assert (project_dir / "program" / "lib.py").exists(), "lib.py not found"
    assert (project_dir / "tests" / "test_program.py").exists(), "test_program.py not found"
    assert (project_dir / "client" / "package.json").exists(), "package.json not found"
    
    # Verify content of key files
    cargo_toml = (project_dir / "Cargo.toml").read_text()
    assert 'anchor-lang = "0.30.1"' in cargo_toml, "Incorrect Cargo.toml content"
    
    anchor_toml = (project_dir / "Anchor.toml").read_text()
    assert TEST_PROGRAM_ID in anchor_toml, "Program ID not found in Anchor.toml"
    
    lib_py = (project_dir / "program" / "lib.py").read_text()
    assert "@program" in lib_py, "Program decorator not found in lib.py"
    assert TEST_PROGRAM_ID in lib_py, "Program ID not found in lib.py"

@pytest.fixture
def mock_solana_config(tmp_path):
    """Create a mock Solana config for testing"""
    config_dir = tmp_path / ".config" / "solana"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "cli" / "config.yml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text(f"""---
json_rpc_url: "{SOLANA_RPC_URL}"
websocket_url: ""
keypair_path: {tmp_path}/id.json
commitment: confirmed
""")
    return config_dir

@pytest.fixture(scope="session")
def event_loop():
    """Create and provide an event loop for async tests.
    
    This is required by pytest-asyncio and must be session-scoped.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
    asyncio.set_event_loop(None)

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
    """Configure Solana CLI to use localnet."""
    # Ensure test validator is running
    ensure_test_validator()
    
    # Set Solana config to use localnet
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
    """Create and fund a test keypair on localnet."""
    print("\n🔑 Setting up funded keypair for tests...")
    
    # Generate new keypair
    keypair_path = TEST_DIR / "test-keypair.json"
    
    # Remove existing keypair if it exists
    if keypair_path.exists():
        keypair_path.unlink()
        
    # Generate new keypair
    subprocess.run(
        ["solana-keygen", "new", "--no-bip39-passphrase", "-o", str(keypair_path), "--force"],
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
    
    print(f"🔑 Generated keypair: {pubkey}")
    
    # Request airdrop (local validator has no rate limits)
    print("🪙 Requesting airdrop...")
    subprocess.run(
        ["solana", "airdrop", "10", pubkey, "--url", SOLANA_RPC_URL],
        check=True,
        capture_output=True
    )
    
    # Wait for confirmation
    print("⏳ Waiting for confirmation...")
    time.sleep(2)
    
    # Verify balance
    balance = subprocess.run(
        ["solana", "balance", pubkey, "--url", SOLANA_RPC_URL],
        check=True,
        capture_output=True,
        text=True
    ).stdout.strip()
    
    print(f"💰 Balance: {balance}")
    
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
