import pytest
import asyncio
import os
import shutil
from pathlib import Path
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from typing import Generator, AsyncGenerator
from dolphin.parser import SolanaParser
from dolphin.dl.parser import DLParser
from dolphin.compiler import compile_program, CompilerConfig
from dolphin.deployer import ProgramDeployer

# Constants for test configuration
TEST_RPC_URL = "http://localhost:8899"
TEST_DIR = Path(__file__).parent
TEST_PROGRAMS_DIR = TEST_DIR / "test_programs"
TEST_OUTPUT_DIR = TEST_DIR / "test_output"
EXAMPLE_PROGRAM_ID = "Test999999999999999999999999999999999999999"

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create and provide an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_dirs() -> Generator[tuple[Path, Path], None, None]:
    """Create and cleanup test directories."""
    TEST_PROGRAMS_DIR.mkdir(exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)
    
    yield TEST_PROGRAMS_DIR, TEST_OUTPUT_DIR
    
    # Cleanup after tests
    shutil.rmtree(TEST_OUTPUT_DIR)
    if TEST_PROGRAMS_DIR.exists():
        shutil.rmtree(TEST_PROGRAMS_DIR)

@pytest.fixture(scope="session")
async def solana_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide a Solana RPC client."""
    async with AsyncClient(TEST_RPC_URL) as client:
        yield client

@pytest.fixture(scope="session")
def payer_keypair() -> Keypair:
    """Provide a funded keypair for tests."""
    return Keypair()

@pytest.fixture(scope="session")
async def funded_payer(
    solana_client: AsyncClient,
    payer_keypair: Keypair
) -> AsyncGenerator[Keypair, None]:
    """Provide a funded keypair for tests."""
    await solana_client.request_airdrop(
        payer_keypair.public_key,
        10_000_000_000  # 10 SOL
    )
    # Wait for confirmation
    await asyncio.sleep(1)
    yield payer_keypair

@pytest.fixture
def example_program_py() -> str:
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
def example_program_dl() -> str:
    """Provide example Dolphin Language program content."""
    return f"""
program ExampleProgram {{
    id: "{EXAMPLE_PROGRAM_ID}"
    
    account Counter {{
        authority: pubkey
        count: u64
    }}
    
    ix initialize(authority: pubkey) {{
        @counter.authority = authority
        @counter.count = 0
    }}
    
    ix increment() {{
        require(@counter.authority == @signer)
        @counter.count += 1
    }}
}}
"""

@pytest.fixture
def compiler_config() -> CompilerConfig:
    """Provide default compiler configuration."""
    return CompilerConfig(
        optimize=True,
        debug_symbols=True,
        target="bpf-unknown-unknown",
        features=[]
    )

@pytest.fixture
async def deployed_program(
    solana_client: AsyncClient,
    funded_payer: Keypair,
    example_program_py: str,
    test_dirs: tuple[Path, Path],
    compiler_config: CompilerConfig
) -> AsyncGenerator[str, None]:
    """Deploy a program and return its ID."""
    programs_dir, output_dir = test_dirs
    program_path = programs_dir / "example_program.py"
    program_path.write_text(example_program_py)
    
    # Parse and compile
    parser = SolanaParser(program_path.read_text())
    ir = parser.parse()
    compilation_result = compile_program(
        ir,
        config=compiler_config,
        output_dir=output_dir
    )
    
    # Deploy
    deployer = ProgramDeployer(
        solana_client,
        funded_payer,
        compilation_result.output_dir
    )
    
    deployment_result = await deployer.deploy()
    yield deployment_result.program_id

@pytest.fixture
def create_test_program():
    """Helper fixture to create test program files."""
    def _create_program(filename: str, content: str) -> Path:
        path = TEST_PROGRAMS_DIR / filename
        path.write_text(content)
        return path
    return _create_program

@pytest.fixture
def parse_and_compile():
    """Helper fixture to parse and compile programs."""
    def _parse_and_compile(
        program_path: Path,
        config: CompilerConfig = None
    ):
        if program_path.suffix == '.py':
            parser = SolanaParser(program_path.read_text())
        else:
            parser = DLParser(program_path.read_text())
            
        ir = parser.parse()
        return compile_program(
            ir,
            config=config or CompilerConfig(),
            output_dir=TEST_OUTPUT_DIR
        )
    return _parse_and_compile

# Custom markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "requires_validator: mark test as requiring a running Solana validator"
    )

@pytest.fixture
def mock_validator(monkeypatch):
    """Mock Solana validator responses for tests."""
    class MockValidator:
        async def get_account_info(self, pubkey):
            return {"lamports": 1000000, "executable": True}
            
        async def request_airdrop(self, pubkey, amount):
            return "transaction_signature"
    
    monkeypatch.setattr(
        "solana.rpc.async_api.AsyncClient",
        lambda _: MockValidator()
    )

@pytest.fixture
def assert_program_structure():
    """Helper fixture to assert program structure."""
    def _assert_structure(program_path: Path, expected_structure: dict):
        if program_path.suffix == '.py':
            parser = SolanaParser(program_path.read_text())
        else:
            parser = DLParser(program_path.read_text())
            
        ir = parser.parse()
        
        assert ir.name == expected_structure.get('name')
        assert ir.program_id == expected_structure.get('program_id')
        
        if 'accounts' in expected_structure:
            assert len(ir.accounts) == len(expected_structure['accounts'])
            
        if 'instructions' in expected_structure:
            assert len(ir.instructions) == len(expected_structure['instructions'])
    
    return _assert_structure

# Environment setup helpers
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ["DOLPHIN_TEST_MODE"] = "1"
    os.environ["SOLANA_NETWORK"] = "localnet"
    yield
    del os.environ["DOLPHIN_TEST_MODE"]
    del os.environ["SOLANA_NETWORK"]