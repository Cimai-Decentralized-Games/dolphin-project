import pytest
import asyncio
import json
import subprocess
from pathlib import Path
from dolphin.ir_gen import IRGenerator
from dolphin import DolphinCompiler

# Test constants
TEST_PROGRAMS_DIR = Path(__file__).parent / "test_programs"
TEST_OUTPUT_DIR = Path(__file__).parent / "test_output"
SOLANA_NETWORK = "devnet"
SOLANA_RPC_URL = "https://api.devnet.solana.com"

class SolanaDeployer:
    """Helper class for Solana program deployment"""
    
    def __init__(self, network_url: str = SOLANA_RPC_URL):
        self.network_url = network_url
        
    def deploy_program(self, program_path: str, keypair_path: str) -> str:
        """Deploy a program using Solana CLI"""
        result = subprocess.run(
            [
                "solana", "program", "deploy",
                "--url", self.network_url,
                "--keypair", keypair_path,
                program_path
            ],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Deployment failed: {result.stderr}")
            
        # Extract program ID from output
        for line in result.stdout.split('\n'):
            if "Program Id:" in line:
                return line.split(":")[1].strip()
        raise RuntimeError("Could not find program ID in deployment output")
        
    def get_account_info(self, pubkey: str) -> dict:
        """Get account info using Solana CLI"""
        result = subprocess.run(
            [
                "solana", "account",
                "--url", self.network_url,
                "--output", "json",
                pubkey
            ],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to get account info: {result.stderr}")
        return json.loads(result.stdout)
        
    def upgrade_program(self, program_path: str, program_id: str, keypair_path: str) -> str:
        """Upgrade an existing program"""
        result = subprocess.run(
            [
                "solana", "program", "deploy",
                "--url", self.network_url,
                "--keypair", keypair_path,
                "--program-id", program_id,
                program_path
            ],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Upgrade failed: {result.stderr}")
        return program_id

@pytest.mark.requires_network
class TestProgramDeployment:
    async def test_deploy_basic_program(self, funded_keypair):
        """Test deploying a basic program"""
        # Create program
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
        
        # Generate IR and compile
        ir_gen = IRGenerator(program_content)
        program_ir = ir_gen.generate()
        
        compiler = DolphinCompiler(
            frontend_path=str(program_path),
            output_path=str(TEST_OUTPUT_DIR)
        )
        compiler.compile(ir_gen)
        
        # Deploy program
        deployer = SolanaDeployer()
        program_id = deployer.deploy_program(
            str(TEST_OUTPUT_DIR / "target" / "deploy" / "program.so"),
            funded_keypair["path"]
        )
        
        # Verify deployment
        account_info = deployer.get_account_info(program_id)
        assert account_info["executable"] is True

    async def test_deploy_upgrade_program(self, funded_keypair):
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
        
        # Generate IR and compile initial version
        ir_gen = IRGenerator(initial_program_content)
        program_ir = ir_gen.generate()
        
        compiler = DolphinCompiler(
            frontend_path=str(program_path),
            output_path=str(TEST_OUTPUT_DIR)
        )
        compiler.compile(ir_gen)
        
        # Deploy initial version
        deployer = SolanaDeployer()
        program_id = deployer.deploy_program(
            str(TEST_OUTPUT_DIR / "target" / "deploy" / "program.so"),
            funded_keypair["path"]
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
        
        # Generate IR and compile upgrade
        ir_gen = IRGenerator(upgraded_program_content)
        program_ir = ir_gen.generate()
        compiler.compile(ir_gen)
        
        # Deploy upgrade
        upgraded_program_id = deployer.upgrade_program(
            str(TEST_OUTPUT_DIR / "target" / "deploy" / "program.so"),
            program_id,
            funded_keypair["path"]
        )
        
        assert upgraded_program_id == program_id

    async def test_deployment_error_handling(self, funded_keypair):
        """Test handling deployment errors"""
        deployer = SolanaDeployer()
        
        # Try to deploy nonexistent program
        with pytest.raises(RuntimeError) as exc_info:
            deployer.deploy_program(
                "nonexistent.so",
                funded_keypair["path"]
            )
        assert "No such file or directory" in str(exc_info.value)
        
        # Try to deploy with invalid keypair
        with pytest.raises(RuntimeError) as exc_info:
            deployer.deploy_program(
                str(TEST_OUTPUT_DIR / "target" / "deploy" / "program.so"),
                "invalid_keypair.json"
            )
        assert "No such file or directory" in str(exc_info.value)
