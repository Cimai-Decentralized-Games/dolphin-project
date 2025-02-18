import pytest
from pathlib import Path
from dolphin.ir_gen import IRGenerator
from dolphin.core.types import SolanaType, AccountDefinition, InstructionDefinition

# Test program source code
TEST_PROGRAM = """
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

@pytest.fixture
def ir_generator():
    """Fixture to create IRGenerator instance with test program"""
    return IRGenerator(TEST_PROGRAM)

def test_program_parsing(ir_generator):
    """Test basic program parsing"""
    program = ir_generator.generate()
    
    assert program is not None
    assert program.program_id == "Test111111111111111111111111111111111111111"
    assert len(program.accounts) == 1
    assert len(program.instructions) == 2

def test_account_processing(ir_generator):
    """Test account processing and type validation"""
    program = ir_generator.generate()
    counter_account = program.accounts[0]
    
    # Test account structure
    assert counter_account.name == "Counter"
    assert len(counter_account.fields) == 2
    
    # Test field types
    authority_field = counter_account.fields[0]
    count_field = counter_account.fields[1]
    
    assert authority_field.name == "authority"
    assert authority_field.type_name == SolanaType.PUBKEY.value
    
    assert count_field.name == "count"
    assert count_field.type_name == SolanaType.U64.value

def test_instruction_processing(ir_generator):
    """Test instruction processing"""
    program = ir_generator.generate()
    
    # Test initialize instruction
    init_instruction = program.instructions[0]
    assert init_instruction.name == "initialize"
    assert len(init_instruction.args) == 1
    assert init_instruction.args[0].name == "authority"
    assert init_instruction.args[0].type_name == SolanaType.PUBKEY.value
    
    # Test increment instruction
    incr_instruction = program.instructions[1]
    assert incr_instruction.name == "increment"
    assert len(incr_instruction.args) == 0

def test_type_validation(ir_generator):
    """Test type validation and normalization"""
    program = ir_generator.generate()
    
    # Test that types are properly normalized
    for account in program.accounts:
        for field in account.fields:
            # Ensure type is a valid Solana type
            assert field.type_name in [t.value for t in SolanaType]

def test_account_validation_generation(ir_generator):
    """Test generation of account validation code"""
    program = ir_generator.generate()
    incr_instruction = program.instructions[1]
    
    # Debugging: Print the instruction body
    for stmt in incr_instruction.body:
        print(f"Statement: {stmt.kind}, Data: {stmt.data}")
    
    # Check that signer validation is added
    has_signer_check = any(
        stmt.kind == "require" and "signer" in stmt.data["message"]
        for stmt in incr_instruction.body
    )
    assert has_signer_check

def test_invalid_type_handling():
    """Test handling of invalid types"""
    INVALID_PROGRAM = """
    from dolphin.prelude import *

    @program("Test111111111111111111111111111111111111111")
    class TestProgram:
        @account
        class Counter:
            value: InvalidType  # Invalid type
    """
    
    ir_generator = IRGenerator(INVALID_PROGRAM)
    with pytest.raises(ValueError, match="Invalid type"):
        ir_generator.generate()

def test_pda_handling(ir_generator):
    """Test PDA account handling"""
    PDA_PROGRAM = """
    from dolphin.prelude import *

    @program("Test111111111111111111111111111111111111111")
    class TestProgram:
        @account
        @pda("authority", "seed")
        class Counter:
            authority: Pubkey
            seed: str
            count: u64
    """
    
    ir_generator = IRGenerator(PDA_PROGRAM)
    program = ir_generator.generate()
    counter_account = program.accounts[0]
    
    assert counter_account.is_pda
    assert counter_account.discriminator == "counter_type"
    assert "authority" in counter_account.seeds
    assert "seed" in counter_account.seeds

def test_complex_type_handling():
    """Test handling of complex types (Vec, Option)"""
    COMPLEX_PROGRAM = """
    from dolphin.prelude import *

    @program("Test111111111111111111111111111111111111111")
    class TestProgram:
        @account
        class ComplexAccount:
            values: Vec<u64>
            maybe_authority: Option<Pubkey>
    """
    
    ir_generator = IRGenerator(COMPLEX_PROGRAM)
    program = ir_generator.generate()
    account = program.accounts[0]
    
    values_field = account.fields[0]
    maybe_field = account.fields[1]
    
    assert values_field.type_name == "Vec<u64>"
    assert maybe_field.type_name == "Option<Pubkey>"

def test_method_call_processing(ir_generator):
    """Test processing of method calls in instructions"""
    program = ir_generator.generate()
    init_instruction = program.instructions[0]
    
    # Find assignment statements
    assignments = [
        stmt for stmt in init_instruction.body 
        if stmt.kind == "assignment"
    ]
    
    assert len(assignments) == 2
    assert any(
        stmt.data["target"] == "counter.authority" 
        for stmt in assignments
    )
    assert any(
        stmt.data["target"] == "counter.count" 
        for stmt in assignments
    )
