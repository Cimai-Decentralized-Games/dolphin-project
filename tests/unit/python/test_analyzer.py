import pytest
from dolphin.analyzer import SolanaAnalyzer
from dolphin.ir import IRProgram, IRAccount, IRInstruction, IRField, IRStatement, IRExpression, IRLiteral, IRVariable, IRBinaryOp

def test_analyze_valid_program():
    """Test analyzing a valid program"""
    program = IRProgram(
        name="TestProgram",
        program_id="Test111111111111111111111111111111111111111",
        accounts=[
            IRAccount(name="Counter", fields=[
                IRField(name="count", type_name="u64")
            ])
        ],
        instructions=[
            IRInstruction(name="increment", args=[], accounts=[], body=[])  # Minimal instruction
        ]
    )

    analyzer = SolanaAnalyzer()
    result = analyzer.analyze(program)
    assert len(analyzer.errors) == 0 # No success attribute

def test_analyze_duplicate_accounts():
    """Test detection of duplicate account definitions"""
    program = IRProgram(
        name="TestProgram",
        program_id="Test111111111111111111111111111111111111111",
        accounts=[
            IRAccount(name="Counter", fields=[]),
            IRAccount(name="Counter", fields=[])  # Duplicate
        ],
        instructions=[]
    )

    analyzer = SolanaAnalyzer()
    result = analyzer.analyze(program)
    assert len(analyzer.errors) > 0
    assert any("duplicate" in err.lower() for err in analyzer.errors)

def test_analyze_invalid_types():
    """Test detection of invalid type usage"""
    program = IRProgram(
        name="TestProgram",
        program_id="Test111111111111111111111111111111111111111",
        accounts=[
            IRAccount(name="Test", fields=[
                IRField(name="invalid", type_name="InvalidType")
            ])
        ],
        instructions=[]
    )

    analyzer = SolanaAnalyzer()
    result = analyzer.analyze(program)
    assert len(analyzer.errors) > 0
    assert any("type" in err.lower() for err in analyzer.errors)