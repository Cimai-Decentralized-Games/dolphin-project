import pytest
from dolphin.parser import SolanaParser
from dolphin.ast import *

def test_parse_basic_program():
    """Test parsing a basic program"""
    source = """
from dolphin.prelude import *

@program("Test111111111111111111111111111111111111111")
class BasicProgram:
    @account
    class Counter:
        count: u64
        
    @instruction
    def increment(self):
        self.counter.count += 1
"""
    parser = SolanaParser(source)
    program = parser.parse()
    
    assert program.name == "BasicProgram"
    assert len(program.accounts) == 1
    assert len(program.instructions) == 1

def test_parse_invalid_syntax():
    """Test parser error handling"""
    source = """
@program("Invalid111111111111111111111111111111111111")
class InvalidProgram
    def broken_method()  # Missing colon and body
"""
    parser = SolanaParser(source)
    with pytest.raises(SyntaxError):
        parser.parse()

def test_parse_type_annotations():
    """Test parsing type annotations"""
    source = """
@account
class TestAccount:
    simple: u64
    complex: List[u8]
    optional: Optional[Pubkey]
"""
    parser = SolanaParser(source)
    account = parser.parse_account(source)
    
    assert len(account.fields) == 3
    assert account.fields[0].type_name == "u64"
    assert "List" in account.fields[1].type_name
    assert "Optional" in account.fields[2].type_name