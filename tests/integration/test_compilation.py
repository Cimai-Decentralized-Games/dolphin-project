import pytest
import os
import shutil
import json
from pathlib import Path
from dolphin.ir import to_json
from dolphin import DolphinCompiler
from dolphin.ir_gen import IRGenerator

TEST_PROGRAMS_DIR = Path(__file__).parent / "test_programs"
TEST_PROGRAMS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = Path(__file__).parent / "output"

TEST_PROGRAM = """
from dolphin.prelude import *

@program("Test111111111111111111111111111111111111111")
class TestProgram:
    @account
    class Counter:
        authority: Pubkey
        count: u64

    @instruction
    def initialize(self, authority: Signer):
        self.counter.authority = authority
        self.counter.count = 0

    @instruction
    def increment(self):
        assert self.counter.count >= 0, "Count cannot be negative"
        self.counter.count += 1
"""

@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for tests"""
    print("\nSetting up test environment...")
    TEST_PROGRAMS_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("Test environment setup complete.")
    
    yield
    
    print("\nTearing down test environment...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    print("Test environment teardown complete.")

def create_test_program(filename: str, content: str):
    """Helper to create test program files"""
    (TEST_PROGRAMS_DIR / "__init__.py").touch()
    path = TEST_PROGRAMS_DIR / filename
    print(f"Creating test program file: {path}")
    path.write_text(content)
    print(f"Test program file created successfully.")
    return path

def debug_and_compile(program_ir, program_path: Path, name: str):
    """Helper to debug and compile IR"""
    print("\nAttempting compilation...")
    
    # Serialize and pretty print the exact JSON being sent to Rust
    final_json = to_json(program_ir)
    print("\nExact JSON being sent to Rust compiler:")
    print(json.dumps(final_json, indent=2))
    
    # Save the exact JSON for debugging
    debug_final_path = OUTPUT_DIR / f"final_{name}_ir.json"
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(debug_final_path, "w") as f:
        json.dump(final_json, f, indent=2)
    print(f"\nSaved final IR to: {debug_final_path}")
    
    # Print detailed structure analysis
    print("\nDetailed IR Analysis:")
    print("1. Instructions:")
    for idx, instr in enumerate(program_ir.instructions):
        print(f"\nInstruction {idx}: {instr.name}")
        print("Arguments:", [f"{arg.name}: {arg.type_name}" for arg in instr.args])
        print("Body statements:", len(instr.body))
        for stmt_idx, stmt in enumerate(instr.body):
            print(f"\n  Statement {stmt_idx}:")
            print(f"    Kind: {stmt.kind}")
            print(f"    Data: {stmt.data}")
            if stmt.kind == "Require":
                require_data = stmt.data.get("data", {})
                print(f"    Require condition: {require_data.get('condition', {})}")
                print(f"    Require message: {require_data.get('message', '')}")
    
    print("\n2. Accounts:")
    for acc in program_ir.accounts:
        print(f"\nAccount: {acc.name}")
        print(f"Is PDA: {acc.is_pda}")
        print(f"Seeds: {acc.seeds}")
        print("Fields:", [f"{f.name}: {f.type_name}" for f in acc.fields])
    
    compiler = DolphinCompiler(
        frontend_path=str(program_path),
        output_path=str(OUTPUT_DIR)
    )
    try:
        compiler.compile(program_ir)
    except Exception as e:
        print(f"\nCompilation failed with error: {str(e)}")
        print("\nError occurred at JSON position:", str(e).split("column")[-1].strip())
        
        # Try to identify the problematic part of the JSON
        error_pos = int(str(e).split("column")[-1].strip())
        json_str = json.dumps(final_json)
        print("\nJSON around error position:")
        start = max(0, error_pos - 50)
        end = min(len(json_str), error_pos + 50)
        print(f"...{json_str[start:error_pos]}>>>ERROR HERE<<< {json_str[error_pos:end]}...")
        raise

@pytest.mark.integration
class TestProgramCompilation:
    def test_compile_basic_python_program(self):
        """Test compiling a basic Python program"""
        print("\nTesting compilation of basic Python program...")

        # Step 1: Create program file
        program_path = create_test_program("test_program.py", TEST_PROGRAM)
        print(f"\nCreated test program at: {program_path}")

        # Step 2: Generate IR
        print("\nGenerating IR...")
        ir_gen = IRGenerator(TEST_PROGRAM)
        program_ir = ir_gen.generate()
        
        # Debug: Print IR before JSON conversion
        print("\nGenerated IR structure:")
        print(f"Program ID: {program_ir.program_id}")
        print(f"Accounts: {len(program_ir.accounts)}")
        for account in program_ir.accounts:
            print(f"  Account {account.name}:")
            for field in account.fields:
                print(f"    Field {field.name}: {field.type_name}")
        print(f"Instructions: {len(program_ir.instructions)}")
        for instruction in program_ir.instructions:
            print(f"  Instruction {instruction.name}:")
            print(f"    Args: {[arg.name for arg in instruction.args]}")
            print(f"    Body: {len(instruction.body)} statements")

        # Step 3: Convert to JSON for debugging
        print("\nConverting IR to JSON...")
        try:
            ir_json = to_json(program_ir)
            print("JSON conversion successful")
            print("JSON structure:")
            print(json.dumps(ir_json, indent=2))
        except Exception as e:
            print(f"JSON conversion failed: {str(e)}")
            raise

        # Step 4: Compile using DolphinCompiler
        debug_and_compile(program_ir, program_path, "basic")

        # Step 5: Verify compilation results
        print("\nVerifying compilation results...")
        
        # Check Anchor.toml
        anchor_toml = OUTPUT_DIR / "Anchor.toml"
        assert anchor_toml.exists(), "Anchor.toml not found"
        anchor_content = anchor_toml.read_text()
        assert "Test111111111111111111111111111111111111111" in anchor_content
        
        # Check Cargo.toml
        cargo_toml = OUTPUT_DIR / "Cargo.toml"
        assert cargo_toml.exists(), "Cargo.toml not found"
        cargo_content = cargo_toml.read_text()
        assert 'anchor-lang = "0.30.1"' in cargo_content
        
        # Check lib.rs
        lib_rs = OUTPUT_DIR / "src" / "lib.rs"
        assert lib_rs.exists(), "lib.rs not found"
        rust_content = lib_rs.read_text()
        assert "#[program]" in rust_content
        assert "pub struct Counter" in rust_content
        assert "pub fn initialize" in rust_content
        assert "pub fn increment" in rust_content

        print("Test compile_basic_python_program PASSED")

    def test_compile_with_validation(self):
        """Test compilation with account validation"""
        print("\nTesting compilation with account validation...")

        program_content = """
from dolphin.prelude import *

@program("Test222222222222222222222222222222222222222")
class ValidatedProgram:
    @account
    class ValidatedAccount:
        owner: Pubkey
        data: Vec<u64>
        settings: Option<Pubkey>

    @instruction
    def initialize(self, owner: Signer):
        self.account.owner = owner
"""
        
        # Step 1: Create program file
        program_path = create_test_program("validated_program.py", program_content)
        
        # Step 2: Generate IR
        print("\nGenerating IR...")
        ir_gen = IRGenerator(program_content)
        program_ir = ir_gen.generate()
        
        # Debug: Print IR before JSON conversion
        print("\nGenerated IR structure:")
        print(f"Program ID: {program_ir.program_id}")
        print(f"Accounts: {len(program_ir.accounts)}")
        for account in program_ir.accounts:
            print(f"  Account {account.name}:")
            for field in account.fields:
                print(f"    Field {field.name}: {field.type_name}")
        
        # Step 3: Convert to JSON for debugging
        print("\nConverting IR to JSON...")
        try:
            ir_json = to_json(program_ir)
            print("JSON conversion successful")
            print("JSON structure:")
            print(json.dumps(ir_json, indent=2))
        except Exception as e:
            print(f"JSON conversion failed: {str(e)}")
            raise

        # Step 4: Compile
        debug_and_compile(program_ir, program_path, "pda")

        # Step 5: Verify Rust output
        lib_rs = OUTPUT_DIR / "src" / "lib.rs"
        assert lib_rs.exists()
        rust_content = lib_rs.read_text()
        
        # Check for proper Rust type conversions
        assert "pub owner: Pubkey" in rust_content
        assert "pub data: Vec<u64>" in rust_content
        assert "pub settings: Option<Pubkey>" in rust_content
        
        print("Test compile_with_validation PASSED")

    def test_compile_with_pda(self):
        """Test compilation with PDA accounts"""
        print("\nTesting compilation with PDA accounts...")

        program_content = """
    from dolphin.prelude import *

    @program("Test333333333333333333333333333333333333333")
    class PDAProgram:
        @account
        @pda(seeds=["vault", "mint"])  # Use proper PDA seeds
        class TokenVault:
            mint: Pubkey     # Mint address as seed
            amount: u64      # Vault balance
            bump: u8         # Store bump for derivation

        @instruction
        def initialize(self, mint: Pubkey, bump: u8):
            self.token_vault.mint = mint
            self.token_vault.amount = 0
            self.token_vault.bump = bump
    """
        
        # Step 1: Create program file
        program_path = create_test_program("pda_program.py", program_content)
        
        # Step 2: Generate IR
        print("\nGenerating IR...")
        ir_gen = IRGenerator(program_content)
        program_ir = ir_gen.generate()
        
        # Debug: Print IR before JSON conversion
        print("\nGenerated IR structure:")
        print(f"Program ID: {program_ir.program_id}")
        print(f"Accounts: {len(program_ir.accounts)}")
        for account in program_ir.accounts:
            print(f"  Account {account.name}:")
            print(f"  Is PDA: {account.is_pda}")
            print(f"  Seeds: {account.seeds}")
            for field in account.fields:
                print(f"    Field {field.name}: {field.type_name}")
        
        # Step 3: Convert to JSON for debugging
        print("\nConverting IR to JSON...")
        try:
            ir_json = to_json(program_ir)
            print("JSON conversion successful")
            print("JSON structure:")
            print(json.dumps(ir_json, indent=2))
        except Exception as e:
            print(f"JSON conversion failed: {str(e)}")
            raise

        # Step 4: Compile
        debug_and_compile(program_ir, program_path, "validation")

        # Step 5: Verify Rust output
        lib_rs = OUTPUT_DIR / "src" / "lib.rs"
        assert lib_rs.exists()
        rust_content = lib_rs.read_text()
        
        # Check for PDA derivation code
        print("\nDebug - Generated Rust content:")
        print(rust_content)
        print("\nDebug - Looking for PDA seeds:")
        print("1. Looking for seeds array...")
        assert "seeds = [" in rust_content, "Seeds array not found"
        print("2. Looking for byte string 'vault'...")
        assert "b\"vault\"" in rust_content, "Byte string 'vault' not found"
        print("3. Looking for mint reference...")
        assert "mint.as_ref()" in rust_content, f"Mint reference not found. Found seeds: {rust_content.split('seeds = [')[1].split(']')[0]}"
        assert "bump" in rust_content
        
        print("Test compile_with_pda PASSED")