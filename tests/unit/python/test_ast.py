import pytest
from dolphin.ast import *

def test_node_creation():
    """Test basic AST node creation"""
    node = Node()
    assert isinstance(node, Node)

def test_program_node():
    """Test Program node structure"""
    statements = [
        VariableDeclaration("counter", "u64", None),
        Assignment("counter", BinaryOp(
            left=Variable("counter"),
            operator="+",
            right=Literal(1)
        ))
    ]
    
    program = Program(statements)
    assert len(program.statements) == 2
    assert isinstance(program.statements[0], VariableDeclaration)
    assert isinstance(program.statements[1], Assignment)

def test_expression_evaluation():
    """Test expression node evaluation"""
    expr = BinaryOp(
        left=Literal(5),
        operator="+",
        right=Literal(3)
    )
    
    assert isinstance(expr.left, Literal)
    assert isinstance(expr.right, Literal)
    assert expr.operator == "+"

def test_account_definition():
    """Test account definition nodes"""
    fields = [
        VariableDeclaration("owner", "Pubkey", None),
        VariableDeclaration("balance", "u64", Literal(0))
    ]
    
    account = AccountDef("TokenAccount", fields)
    assert account.name == "TokenAccount"
    assert len(account.fields) == 2