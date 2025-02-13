import pytest
import os
import shutil
from pathlib import Path
from dolphin.compiler import compile_program
from dolphin.parser import SolanaParser
from dolphin.dl.parser import DLParser

TEST_PROGRAMS_DIR = Path(__file__).parent / "test_programs"
OUTPUT_DIR = Path(__file__).parent / "output"

@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for tests"""
    # Setup
    TEST_PROGRAMS_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    yield
    
    # Teardown
    shutil.rmtree(OUTPUT_DIR)

def create_test_program(filename: str, content: str):
    """Helper to create test program files"""
    path = TEST_PROGRAMS_DIR / filename
    path.write_text(content)
    return path

@pytest.mark.integration
class TestProgramCompilation:
    def test_compile_basic_python_program(self):
        """Test compiling a basic Python program"""
        program_content = """
from dolphin.prelude import *

@program("Test111111111111111111111111111111111111111")
class TestProgram:
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
        program_path = create_test_program("basic_program.py", program_content)
        
        # Parse and compile
        parser = SolanaParser(program_path.read_text())
        ir = parser.parse()
        result = compile_program(ir)
        
        # Verify compilation result
        assert result.success
        assert result.output_dir.exists()
        assert (result.output_dir / "lib.rs").exists()
        
        # Verify program structure
        lib_rs = (result.output_dir / "lib.rs").read_text()
        assert "#[program]" in lib_rs
        assert "pub struct Counter" in lib_rs
        assert "pub fn initialize" in lib_rs
        assert "pub fn increment" in lib_rs

    def test_compile_dl_program(self):
        """Test compiling a Dolphin Language program"""
        program_content = """
program TokenVault {
    id: "Vault9999999999999999999999999999999999999"
    
    account VaultState {
        authority: pubkey
        token_mint: pubkey
        total_deposits: u64
    }
    
    ix initialize(authority: pubkey, token_mint: pubkey) {
        require(@signer == authority, "Only authority can initialize")
        @vault.authority = authority
        @vault.token_mint = token_mint
        @vault.total_deposits = 0
    }
}
"""
        program_path = create_test_program("token_vault.dl", program_content)
        
        # Parse and compile
        parser = DLParser(program_path.read_text())
        ir = parser.parse()
        result = compile_program(ir)
        
        # Verify compilation result
        assert result.success
        assert result.output_dir.exists()
        assert (result.output_dir / "lib.rs").exists()

    def test_compile_program_with_pdas(self):
        """Test compiling a program with PDAs"""
        program_content = """
from dolphin.prelude import *

@program("Test222222222222222222222222222222222222222")
class TestProgram:
    @account
    @pda("owner", "mint")
    class TokenAccount:
        owner: Pubkey
        mint: Pubkey
        amount: u64

    @instruction
    def initialize(self, owner: Pubkey, mint: Pubkey):
        self.token_account.owner = owner
        self.token_account.mint = mint
        self.token_account.amount = 0
"""
        program_path = create_test_program("pda_program.py", program_content)
        
        parser = SolanaParser(program_path.read_text())
        ir = parser.parse()
        result = compile_program(ir)
        
        assert result.success
        lib_rs = (result.output_dir / "lib.rs").read_text()
        assert "seeds =" in lib_rs
        assert "bump" in lib_rs

    def test_compile_error_handling(self):
        """Test compilation error handling"""
        program_content = """
from dolphin.prelude import *

@program("Test333333333333333333333333333333333333333")
class TestProgram:
    @account
    class InvalidAccount:
        # Invalid type
        balance: invalid_type

    @instruction
    def initialize(self):
        pass
"""
        program_path = create_test_program("invalid_program.py", program_content)
        
        parser = SolanaParser(program_path.read_text())
        with pytest.raises(Exception) as exc_info:
            ir = parser.parse()
        assert "Invalid type" in str(exc_info.value)

    @pytest.mark.parametrize("optimization_level", [0, 1, 2, 3])
    def test_compile_with_different_optimizations(self, optimization_level):
        """Test compiling with different optimization levels"""
        program_content = """
from dolphin.prelude import *

@program("Test444444444444444444444444444444444444444")
class TestProgram:
    @account
    class Counter:
        count: u64

    @instruction
    def increment(self):
        self.counter.count += 1
"""
        program_path = create_test_program(
            f"optimized_program_{optimization_level}.py",
            program_content
        )
        
        parser = SolanaParser(program_path.read_text())
        ir = parser.parse()
        result = compile_program(ir, optimization_level=optimization_level)
        
        assert result.success