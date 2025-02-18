import pytest
import os
import shutil
from pathlib import Path
import json  
from dolphin.ir import to_json  
from dolphin import DolphinCompiler
from dolphin.ir_gen import IRGenerator  # ✅ Import IR Generator

TEST_PROGRAMS_DIR = Path(__file__).parent / "test_programs"
TEST_PROGRAMS_DIR.mkdir(parents=True, exist_ok=True)  # Ensure it exists
OUTPUT_DIR = Path(__file__).parent / "output"

@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for tests"""
    print("\nSetting up test environment...")
    TEST_PROGRAMS_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("Test environment setup complete.")
    
    yield
    
    print("\nTearing down test environment...")
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

print(f"TEST_PROGRAMS_DIR: {TEST_PROGRAMS_DIR} (Exists: {TEST_PROGRAMS_DIR.exists()})")
print(f"OUTPUT_DIR: {OUTPUT_DIR} (Exists: {OUTPUT_DIR.exists()})")

@pytest.mark.integration
class TestProgramCompilation:
    def test_compile_basic_python_program_dolphin(self):
        """Test generating IR and compiling a Python program"""
        print("\nTesting IR generation and compilation of basic Python program...")

        # ✅ Step 1: Generate IR using `IRGenerator`
        ir_gen = IRGenerator()
        ir_gen.process_program("TestProgram", "Test111111111111111111111111111111111111111")
        ir_gen.process_account("Counter", [
            ("authority", "Pubkey"),
            ("count", "u64")
        ])
        ir_gen.process_instruction("initialize", [
            ("authority", "Pubkey")
        ])
        ir_gen.process_instruction("increment", [])

        # ✅ Step 2: Generate Python code and save it
        print("\nGenerating Python Program...")
        generated_python_code = ir_gen.finalize()  # ✅ Use `finalize()` instead of `generate_ir()`
        python_file_path = TEST_PROGRAMS_DIR / "generated_test_program.py"
        python_file_path.write_text(generated_python_code)
        print(f"Generated Python program saved to: {python_file_path}")

        # ✅ Step 3: Verify that generated Python program matches expected structure
        print("\nGenerated Python Program Content:")
        print(generated_python_code)
        assert "class TestProgram" in generated_python_code
        assert "@instruction" in generated_python_code
        assert "def initialize(self, authority: Pubkey):" in generated_python_code
        assert "def increment(self):" in generated_python_code

        # ✅ Step 4: Compile IR using DolphinCompiler
        print("Instantiating DolphinCompiler...")
        compiler = DolphinCompiler("dolphin.parser", str(OUTPUT_DIR.resolve()))
        compiler.compile(ir_gen)  # ✅ Compile directly from `ir_gen`
        print("Parsing and compilation complete.")

        # ✅ Step 5: Verify compilation results
        print("\nVerifying compilation result...")
        assert (OUTPUT_DIR / "src").exists(), "src directory not found"
        assert (OUTPUT_DIR / "src" / "lib.rs").exists(), "lib.rs not found in src directory"
        assert (OUTPUT_DIR / "Cargo.toml").exists(), "Cargo.toml not found"
        assert (OUTPUT_DIR / "Anchor.toml").exists(), "Anchor.toml not found"

        print("Test compile_basic_python_program_dolphin PASSED")
