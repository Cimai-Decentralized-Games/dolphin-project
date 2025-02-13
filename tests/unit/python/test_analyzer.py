import pytest
from dolphin.analyzer import SolanaAnalyzer
from dolphin.ast import *

def test_analyze_valid_program():
    """Test analyzing a valid program"""
    program = Program(
        name="TestProgram",
        program_id="Test111111111111111111111111111111111111111",
        accounts=[
            AccountDef("Counter", [
                VariableDeclaration("count", "u64", None)
            ])
        ],
        instructions=[
            Instruction("increment", [], [
                Assignment("count", BinaryOp(
                    Variable("count"), "+", Literal(1)
                ))
            ])
        ]
    )
    
    analyzer = SolanaAnalyzer()
    result = analyzer.analyze(program)
    assert result.success
    assert len(result.errors) == 0

def test_analyze_duplicate_accounts():
    """Test detection of duplicate account definitions"""
    program = Program(
        name="TestProgram",
        program_id="Test111111111111111111111111111111111111111",
        accounts=[
            AccountDef("Counter", []),
            AccountDef("Counter", [])  # Duplicate
        ],
        instructions=[]
    )
    
    analyzer = SolanaAnalyzer()
    result = analyzer.analyze(program)
    assert not result.success
    assert any("duplicate" in str(err).lower() for err in result.errors)

def test_analyze_invalid_types():
    """Test detection of invalid type usage"""
    program = Program(
        name="TestProgram",
        program_id="Test111111111111111111111111111111111111111",
        accounts=[
            AccountDef("Test", [
                VariableDeclaration("invalid", "InvalidType", None)
            ])
        ],
        instructions=[]
    )
    
    analyzer = SolanaAnalyzer()
    result = analyzer.analyze(program)
    assert not result.success
    assert any("type" in str(err).lower() for err in result.errors)