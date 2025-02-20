import pytest
import asyncio
import json
import subprocess
import shutil
import time
from pathlib import Path
from dolphin.ir_gen import IRGenerator
from dolphin import DolphinCompiler

# Test constants
TEST_PROGRAMS_DIR = Path(__file__).parent / "test_programs"
TEST_OUTPUT_DIR = Path(__file__).parent / "test_output"
SOLANA_NETWORK = "localnet"
SOLANA_RPC_URL = "http://localhost:8899"

# Create test directories if they don't exist
TEST_PROGRAMS_DIR.mkdir(exist_ok=True)
TEST_OUTPUT_DIR.mkdir(exist_ok=True)

def compile_and_build(program_path: Path, program_ir) -> None:
    """Compile program and build with anchor"""
    # Clean up test output directory
    if TEST_OUTPUT_DIR.exists():
        shutil.rmtree(TEST_OUTPUT_DIR)
    TEST_OUTPUT_DIR.mkdir(parents=True)
    
    # Create directories
    target_dir = TEST_OUTPUT_DIR / "target" / "deploy"
    target_dir.mkdir(parents=True, exist_ok=True)
    src_dir = TEST_OUTPUT_DIR / "src"
    src_dir.mkdir(exist_ok=True)
    
    # Get program name and ID from IR
    # Sanitize program name for Rust - convert to snake case and remove invalid chars
    program_name = program_ir.name.lower().replace(" ", "_").replace("-", "_")
    program_name = "".join(c for c in program_name if c.isalnum() or c == "_")
    if program_name[0].isdigit():
        program_name = "program_" + program_name
    program_id = program_ir.program_id
    
    # Create Cargo.toml
    cargo_toml = TEST_OUTPUT_DIR / "Cargo.toml"
    cargo_toml.write_text(f"""
[package]
name = "{program_name}"
version = "0.1.0"
description = "Created with Dolphin"
edition = "2021"

[lib]
crate-type = ["cdylib", "lib"]

[dependencies]
anchor-lang = "0.30.1"
""")
    
    # Create Anchor.toml
    anchor_toml = TEST_OUTPUT_DIR / "Anchor.toml"
    anchor_toml.write_text(f"""
[features]
seeds = false

[programs.localnet]
{program_name} = "{program_id}"

[registry]
url = "https://anchor.projectserum.com"

[provider]
cluster = "localnet"
wallet = "~/.config/solana/id.json"
""")
    
    # Create lib.rs
    lib_rs = src_dir / "lib.rs"
    lib_rs.write_text(f"""
use anchor_lang::prelude::*;

declare_id!("{program_id}");

#[program]
pub mod {program_name} {{
    use super::*;
    
    pub fn initialize(_ctx: Context<Initialize>) -> Result<()> {{
        Ok(())
    }}
}}

#[derive(Accounts)]
pub struct Initialize {{}}
""")
    
    # Compile program
    print("\n🏗️  Compiling program...")
    compiler = DolphinCompiler(
        frontend_path=str(program_path),
        output_path=str(TEST_OUTPUT_DIR)
    )
    compiler.compile(program_ir)
    print("✨ Program compilation successful")
    
    # Build using cargo build-bpf
    print("\n🔨 Building program with cargo build-bpf...")
    
    # Clean up any previous build artifacts
    target_dir = TEST_OUTPUT_DIR / "target"
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)
    
    # Create deploy directory
    deploy_dir = target_dir / "deploy"
    deploy_dir.mkdir(parents=True, exist_ok=True)
    
    # Debug: List files before build
    print("\nFiles before build:")
    subprocess.run(["ls", "-R", str(TEST_OUTPUT_DIR)], check=True)
    
    # Build using cargo build-bpf
    build_result = subprocess.run(
        [
            "cargo", "build-bpf",
            f"--manifest-path={TEST_OUTPUT_DIR}/Cargo.toml",
            f"--bpf-out-dir={deploy_dir}"
        ],
        capture_output=True,
        text=True
    )
    
    # Always print build output for debugging
    print("\nBuild stdout:")
    print(build_result.stdout)
    print("\nBuild stderr:")
    print(build_result.stderr)
    
    if build_result.returncode != 0:
        print(f"❌ Cargo build-bpf failed!")
        raise RuntimeError(f"Cargo build-bpf failed: {build_result.stderr}")
    
    # Debug: List files after build
    print("\nFiles after build:")
    subprocess.run(["ls", "-R", str(TEST_OUTPUT_DIR)], check=True)
    
    # Check if program.so exists - cargo build-bpf outputs with -keypair.json suffix
    program_files = list(deploy_dir.glob("*.so"))
    if not program_files:
        print(f"\n❌ No .so files found in {deploy_dir}")
        raise RuntimeError("Cargo build-bpf succeeded but no .so files found")
        
    # Rename the first .so file to program.so
    program_so = deploy_dir / "program.so"
    program_files[0].rename(program_so)
    
    print("✨ Program build successful")

# Ensure test validator is running
def ensure_validator_running():
    """Start test validator if not running"""
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

class SolanaDeployer:
    """Helper class for Solana program deployment"""
    
    def __init__(self, network_url: str = SOLANA_RPC_URL):
        self.network_url = network_url
        
    def deploy_program(self, program_path: str, keypair_path: str) -> str:
        """Deploy a program using Solana CLI"""
        print(f"\n🚀 Deploying program to {SOLANA_NETWORK}...")
        print(f"Program path: {program_path}")
        print(f"Using keypair: {keypair_path}")
        
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
            print(f"❌ Deployment failed!")
            print(f"Error: {result.stderr}")
            raise RuntimeError(f"Deployment failed: {result.stderr}")
            
        # Extract program ID from output
        for line in result.stdout.split('\n'):
            if "Program Id:" in line:
                program_id = line.split(":")[1].strip()
                print(f"✨ Successfully deployed program: {program_id}")
                return program_id
        raise RuntimeError("Could not find program ID in deployment output")
        
    def get_account_info(self, pubkey: str) -> dict:
        """Get account info using Solana CLI"""
        print(f"\n📊 Getting account info for: {pubkey}")
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
            print(f"❌ Failed to get account info!")
            print(f"Error: {result.stderr}")
            raise RuntimeError(f"Failed to get account info: {result.stderr}")
        print("✨ Successfully retrieved account info")
        return json.loads(result.stdout)
        
    def upgrade_program(self, program_path: str, program_id: str, keypair_path: str) -> str:
        """Upgrade an existing program"""
        print(f"\n🔄 Upgrading program: {program_id}")
        print(f"New program path: {program_path}")
        print(f"Using keypair: {keypair_path}")
        
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
            print(f"❌ Upgrade failed!")
            print(f"Error: {result.stderr}")
            raise RuntimeError(f"Upgrade failed: {result.stderr}")
        print(f"✨ Successfully upgraded program: {program_id}")
        return program_id

@pytest.mark.requires_network
@pytest.mark.asyncio  # Mark class for pytest-asyncio
class TestProgramDeployment:
    @classmethod
    def setup_class(cls):
        """Ensure test validator is running before any tests"""
        ensure_validator_running()
        
    @pytest.mark.asyncio
    async def test_deploy_basic_program(self, funded_keypair):
        """Test deploying a basic program"""
        print("\n📝 Testing basic program deployment...")
        print(f"Using keypair with public key: {funded_keypair['pubkey']}")
        
        print("\n📄 Creating program source...")
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
        print(f"\n💾 Writing program to: {program_path}")
        program_path.write_text(program_content)
        print("✨ Program file created successfully")
        
        print("\n🔨 Generating IR...")
        ir_gen = IRGenerator(program_content)
        program_ir = ir_gen.generate()
        print("✨ IR generation successful")
        
        compile_and_build(program_path, program_ir)
        
        # Deploy program
        deployer = SolanaDeployer()
        program_id = deployer.deploy_program(
            str(TEST_OUTPUT_DIR / "target" / "deploy" / "program.so"),
            funded_keypair["path"]
        )
        
        # Verify deployment
        print("\n🔍 Verifying program deployment...")
        account_info = deployer.get_account_info(program_id)
        assert account_info["executable"] is True
        print("✅ Program successfully verified as executable")

    @pytest.mark.asyncio
    async def test_deploy_upgrade_program(self, funded_keypair):
        """Test upgrading an existing program"""
        print("\n🔄 Testing program upgrade...")
        print(f"Using keypair with public key: {funded_keypair['pubkey']}")
        
        print("\n📄 Creating initial program version...")
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
        print(f"\n💾 Writing initial program to: {program_path}")
        program_path.write_text(initial_program_content)
        print("✨ Initial program file created successfully")
        
        print("\n🔨 Generating IR for initial version...")
        ir_gen = IRGenerator(initial_program_content)
        program_ir = ir_gen.generate()
        print("✨ Initial IR generation successful")
        
        compile_and_build(program_path, program_ir)
        
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
        print("\n💾 Writing upgraded program version...")
        program_path.write_text(upgraded_program_content)
        print("✨ Upgrade file created successfully")
        
        print("\n🔨 Generating IR for upgrade...")
        ir_gen = IRGenerator(upgraded_program_content)
        program_ir = ir_gen.generate()
        print("✨ Upgrade IR generation successful")
        
        compile_and_build(program_path, program_ir)
        
        # Deploy upgrade
        upgraded_program_id = deployer.upgrade_program(
            str(TEST_OUTPUT_DIR / "target" / "deploy" / "program.so"),
            program_id,
            funded_keypair["path"]
        )
        
        assert upgraded_program_id == program_id
        print("\n✅ Program upgrade test completed successfully")

    @pytest.mark.asyncio
    async def test_deployment_error_handling(self, funded_keypair):
        """Test handling deployment errors"""
        print("\n⚠️ Testing deployment error handling...")
        deployer = SolanaDeployer()
        
        print("\n🔍 Testing deployment of nonexistent program...")
        with pytest.raises(RuntimeError) as exc_info:
            deployer.deploy_program(
                "nonexistent.so",
                funded_keypair["path"]
            )
        assert "No such file or directory" in str(exc_info.value)
        print("✅ Nonexistent program error handled correctly")
        
        print("\n🔍 Testing deployment with invalid keypair...")
        # Try to deploy with invalid keypair
        with pytest.raises(RuntimeError) as exc_info:
            deployer.deploy_program(
                str(TEST_OUTPUT_DIR / "target" / "deploy" / "program.so"),
                "invalid_keypair.json"
            )
        assert "No default signer found" in str(exc_info.value)
        print("✅ Invalid keypair error handled correctly")
        print("\n✅ All error handling tests completed successfully")