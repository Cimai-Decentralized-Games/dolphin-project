import pytest
import asyncio
import json
import subprocess
from pathlib import Path
from dolphin.deployer import ProgramDeployer
from dolphin.compiler import compile_program
from dolphin.parser import SolanaParser

# Test constants
TEST_RPC_URL = "http://localhost:8899"  # Local validator
TEST_PROGRAMS_DIR = Path(__file__).parent / "test_programs"
JS_DIR = Path(__file__).parent.parent / "js"

class SolanaTestClient:
    def __init__(self, network_url: str = TEST_RPC_URL):
        self.network_url = network_url
        self.js_path = JS_DIR

    def _run_js_command(self, *args) -> str:
        result = subprocess.run(
            ["node", "-r", "ts-node/register", "src/solana-test-utils.ts", *args],
            cwd=self.js_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"JavaScript command failed: {result.stderr}")
        return result.stdout.strip()

    def create_keypair(self) -> dict:
        result = self._run_js_command("create-keypair")
        return json.loads(result)

    def request_airdrop(self, public_key: str, amount: float = 2.0) -> str:
        return self._run_js_command("airdrop", public_key, str(amount))

    def deploy_program(self, program_path: str, payer_keypair: dict) -> str:
        temp_keypair_path = self.js_path / "temp_keypair.json"
        with open(temp_keypair_path, 'w') as f:
            json.dump(payer_keypair, f)
        
        try:
            return self._run_js_command("deploy", str(program_path), str(temp_keypair_path))
        finally:
            if temp_keypair_path.exists():
                temp_keypair_path.unlink()

    def get_account_info(self, public_key: str) -> dict:
        result = self._run_js_command("get-account-info", public_key)
        return json.loads(result)

    def upgrade_program(self, program_path: str, program_id: str, payer_keypair: dict) -> str:
        temp_keypair_path = self.js_path / "temp_keypair.json"
        with open(temp_keypair_path, 'w') as f:
            json.dump(payer_keypair, f)
        
        try:
            return self._run_js_command("upgrade", str(program_path), program_id, str(temp_keypair_path))
        finally:
            if temp_keypair_path.exists():
                temp_keypair_path.unlink()

@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
def solana_client():
    """Create a Solana client connected to local validator"""
    return SolanaTestClient()

@pytest.fixture(scope="module")
def payer_keypair(solana_client):
    """Create a keypair for paying deployment fees"""
    return solana_client.create_keypair()

@pytest.fixture(scope="module")
def funded_payer(solana_client, payer_keypair):
    """Fund the payer account"""
    solana_client.request_airdrop(payer_keypair["publicKey"], 10.0)  # 10 SOL
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
        
        program_id = solana_client.deploy_program(
            str(compile_result.output_dir / "lib.so"),
            funded_payer
        )
        
        assert program_id is not None
        
        # Verify deployment
        account_info = solana_client.get_account_info(program_id)
        assert account_info is not None
        assert account_info["executable"]

    async def test_deploy_upgrade_program(self, solana_client, funded_payer):
        """Test upgrading an existing program"""
        # Deploy initial version
        initial_program_content = """
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
        program_path.write_text(initial_program_content)
        
        parser = SolanaParser(program_path.read_text())
        ir = parser.parse()
        compile_result = compile_program(ir)
        
        initial_program_id = solana_client.deploy_program(
            str(compile_result.output_dir / "lib.so"),
            funded_payer
        )
        
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
        
        upgrade_result = solana_client.upgrade_program(
            str(compile_result.output_dir / "lib.so"),
            initial_program_id,
            funded_payer
        )
        
        assert upgrade_result is not None

    @pytest.mark.parametrize("network", ["localnet", "devnet", "testnet"])
    async def test_deploy_to_different_networks(self, network, solana_client, funded_payer):
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
        
        network_client = SolanaTestClient(network=network)
        
        program_id = network_client.deploy_program(
            str(compile_result.output_dir / "lib.so"),
            funded_payer
        )
        
        assert program_id is not None

    async def test_deployment_error_handling(self, solana_client, funded_payer):
        """Test handling deployment errors"""
        # Try to deploy invalid program
        with pytest.raises(Exception) as exc_info:
            solana_client.deploy_program(
                "nonexistent.so",
                funded_payer
            )
        assert "Program file not found" in str(exc_info.value)
        
        # Try to deploy with insufficient funds
        unfunded_payer = solana_client.create_keypair()
        
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
            solana_client.deploy_program(
                str(compile_result.output_dir / "lib.so"),
                unfunded_payer
            )
        assert "insufficient funds" in str(exc_info.value).lower()