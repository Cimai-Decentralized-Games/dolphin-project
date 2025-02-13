import pytest
import asyncio
from pathlib import Path
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.system_program import create_account
from solana.transaction import Transaction
from dolphin.deployer import ProgramDeployer
from dolphin.compiler import compile_program
from dolphin.parser import SolanaParser

# Test constants
TEST_RPC_URL = "http://localhost:8899"  # Local validator
TEST_PROGRAMS_DIR = Path(__file__).parent / "test_programs"

@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def solana_client():
    """Create a Solana client connected to local validator"""
    async with AsyncClient(TEST_RPC_URL) as client:
        yield client

@pytest.fixture(scope="module")
def payer_keypair():
    """Create a keypair for paying deployment fees"""
    return Keypair()

@pytest.fixture(scope="module")
async def funded_payer(solana_client, payer_keypair):
    """Fund the payer account"""
    airdrop_amount = 10_000_000_000  # 10 SOL
    await solana_client.request_airdrop(
        payer_keypair.public_key,
        airdrop_amount
    )
    return payer_keypair

@pytest.mark.integration
class TestProgramDeployment:
    async def test_deploy_basic_program(self, solana_client, funded_payer):
        """Test deploying a basic program"""
        # Compile program
        program_content = """
from dolphin.prelude import *

@program("Test555555555555555555555555555555555555555")
class TestProgram:
    @account
    class Counter:
        count: u64

    @instruction
    def increment(self):
        self.counter.count += 1
"""
        program_path = TEST_PROGRAMS_DIR / "deploy_test.py"
        program_path.write_text(program_content)
        
        parser = SolanaParser(program_path.read_text())
        ir = parser.parse()
        compile_result = compile_program(ir)
        
        assert compile_result.success
        
        # Deploy program
        deployer = ProgramDeployer(
            client=solana_client,
            payer=funded_payer
        )
        
        deploy_result = await deployer.deploy(
            program_path=compile_result.output_dir / "lib.so",
            program_id=Keypair()  # New program keypair
        )
        
        assert deploy_result.success
        assert deploy_result.program_id is not None
        
        # Verify deployment
        account_info = await solana_client.get_account_info(
            deploy_result.program_id.public_key
        )
        assert account_info is not None
        assert len(account_info.data) > 0

    async def test_deploy_upgrade_program(self, solana_client, funded_payer):
        """Test upgrading an existing program"""
        # Deploy initial version
        initial_program_id = Keypair()
        program_content = """
from dolphin.prelude import *

@program("Test666666666666666666666666666666666666666")
class TestProgram:
    @account
    class Counter:
        count: u64

    @instruction
    def increment(self):
        self.counter.count += 1
"""
        program_path = TEST_PROGRAMS_DIR / "upgrade_test.py"
        program_path.write_text(program_content)
        
        parser = SolanaParser(program_path.read_text())
        ir = parser.parse()
        compile_result = compile_program(ir)
        
        deployer = ProgramDeployer(
            client=solana_client,
            payer=funded_payer
        )
        
        initial_deploy = await deployer.deploy(
            program_path=compile_result.output_dir / "lib.so",
            program_id=initial_program_id
        )
        assert initial_deploy.success
        
        # Deploy upgrade
        upgraded_program_content = """
from dolphin.prelude import *

@program("Test666666666666666666666666666666666666666")
class TestProgram:
    @account
    class Counter:
        count: u64
        owner: Pubkey

    @instruction
    def increment(self):
        self.counter.count += 1
"""
        program_path.write_text(upgraded_program_content)
        
        parser = SolanaParser(program_path.read_text())
        ir = parser.parse()
        compile_result = compile_program(ir)
        
        upgrade_result = await deployer.upgrade(
            program_path=compile_result.output_dir / "lib.so",
            program_id=initial_program_id,
            buffer_keypair=Keypair()
        )
        
        assert upgrade_result.success

    @pytest.mark.parametrize("network", ["localnet", "devnet", "testnet"])
    async def test_deploy_to_different_networks(
        self,
        network,
        solana_client,
        funded_payer
    ):
        """Test deploying to different networks"""
        program_content = """
from dolphin.prelude import *

@program("Test777777777777777777777777777777777777777")
class TestProgram:
    @account
    class Counter:
        count: u64

    @instruction
    def increment(self):
        self.counter.count += 1
"""
        program_path = TEST_PROGRAMS_DIR / f"network_test_{network}.py"
        program_path.write_text(program_content)
        
        parser = SolanaParser(program_path.read_text())
        ir = parser.parse()
        compile_result = compile_program(ir)
        
        deployer = ProgramDeployer(
            client=solana_client,
            payer=funded_payer,
            network=network
        )
        
        deploy_result = await deployer.deploy(
            program_path=compile_result.output_dir / "lib.so",
            program_id=Keypair()
        )
        
        assert deploy_result.success

    async def test_deployment_error_handling(
        self,
        solana_client,
        funded_payer
    ):
        """Test handling deployment errors"""
        # Try to deploy invalid program
        deployer = ProgramDeployer(
            client=solana_client,
            payer=funded_payer
        )
        
        with pytest.raises(Exception) as exc_info:
            await deployer.deploy(
                program_path=Path("nonexistent.so"),
                program_id=Keypair()
            )
        assert "Program file not found" in str(exc_info.value)
        
        # Try to deploy with insufficient funds
        unfunded_payer = Keypair()
        deployer = ProgramDeployer(
            client=solana_client,
            payer=unfunded_payer
        )
        
        program_path = TEST_PROGRAMS_DIR / "error_test.py"
        program_path.write_text("""
from dolphin.prelude import *

@program("Test888888888888888888888888888888888888888")
class TestProgram:
    pass
""")
        
        parser = SolanaParser(program_path.read_text())
        ir = parser.parse()
        compile_result = compile_program(ir)
        
        with pytest.raises(Exception) as exc_info:
            await deployer.deploy(
                program_path=compile_result.output_dir / "lib.so",
                program_id=Keypair()
            )
        assert "insufficient funds" in str(exc_info.value).lower()