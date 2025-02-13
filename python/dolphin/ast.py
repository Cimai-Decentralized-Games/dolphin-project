from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any

@dataclass
class Node:
    """Base class for AST nodes with source location tracking"""
    line: int = field(default=0)
    column: int = field(default=0)
    end_line: int = field(default=0)
    end_column: int = field(default=0)

@dataclass
class Program(Node):
    """Top-level program node"""
    name: str
    program_id: str
    statements: List['Statement'] = field(default_factory=list)
    accounts: List['AccountDef'] = field(default_factory=list)
    instructions: List['InstructionDef'] = field(default_factory=list)

@dataclass
class Statement(Node):
    """Base class for all statement nodes"""
    pass

@dataclass
class Expression(Node):
    """Base class for all expression nodes"""
    pass

@dataclass
class AccountDef(Node):
    """Account structure definition"""
    name: str
    fields: List['FieldDef']
    is_pda: bool = False
    seeds: List[str] = field(default_factory=list)
    discriminator: Optional[str] = None

@dataclass
class FieldDef(Node):
    """Account field definition"""
    name: str
    type_name: str
    attributes: List[str] = field(default_factory=list)
    default_value: Optional[Expression] = None

@dataclass
class InstructionDef(Node):
    """Instruction definition"""
    name: str
    args: List['ArgumentDef']
    accounts: List['AccountUsage']
    body: List[Statement]
    return_type: Optional[str] = None

@dataclass
class ArgumentDef(Node):
    """Instruction argument definition"""
    name: str
    type_name: str
    default_value: Optional[Expression] = None

@dataclass
class AccountUsage(Node):
    """Account usage in instruction context"""
    name: str
    account_type: str
    is_mutable: bool = False
    is_signer: bool = False
    is_optional: bool = False

@dataclass
class FunctionDef(Statement):
    """Function definition"""
    name: str
    params: List[ArgumentDef]
    body: List[Statement]
    decorators: List[str] = field(default_factory=list)
    return_type: Optional[str] = None

@dataclass
class VariableDeclaration(Statement):
    """Variable declaration with type annotation"""
    name: str
    type_name: Optional[str]
    value: Expression
    is_mutable: bool = True

@dataclass
class Assignment(Statement):
    """Assignment statement"""
    target: Union[str, 'AttributeAccess']
    value: Expression
    operator: str = "="  # For compound assignments like +=, -=, etc.

@dataclass
class AttributeAccess(Expression):
    """Attribute access (e.g., account.field)"""
    object_name: str
    attribute: str

@dataclass
class MethodCall(Statement):
    """Method call statement"""
    target: AttributeAccess
    method: str
    args: List[Expression]

@dataclass
class BinaryOp(Expression):
    """Binary operation"""
    left: Expression
    operator: str
    right: Expression

@dataclass
class Call(Expression):
    """Function call"""
    function: Union[str, AttributeAccess]
    arguments: List[Expression]
    keywords: Dict[str, Expression] = field(default_factory=dict)

@dataclass
class Literal(Expression):
    """Literal value"""
    value: Union[int, float, str, bool]
    type_name: Optional[str] = None

@dataclass
class VariableReference(Expression):
    """Variable reference"""
    name: str

@dataclass
class DecoratorDef(Node):
    """Decorator definition"""
    name: str
    args: List[Expression] = field(default_factory=list)
    keywords: Dict[str, Expression] = field(default_factory=dict)

@dataclass
class ErrorNode(Node):
    """Error node for graceful error handling"""
    message: str
    original_node: Optional[Any] = None

def create_error(message: str, node: Optional[Node] = None) -> ErrorNode:
    """Helper function to create error nodes"""
    return ErrorNode(
        message=message,
        original_node=node,
        line=node.line if node else 0,
        column=node.column if node else 0,
        end_line=node.end_line if node else 0,
        end_column=node.end_column if node else 0
    )

# Type aliases for clarity
SolanaType = Union[str, 'ArrayType', 'OptionType']

@dataclass
class ArrayType:
    """Array type definition"""
    element_type: SolanaType
    size: Optional[int] = None

@dataclass
class OptionType:
    """Option type definition"""
    inner_type: SolanaType

def parse_type(type_str: str) -> SolanaType:
    """Parse type string into type structure"""
    if type_str.startswith("Vec<") and type_str.endswith(">"):
        inner = type_str[4:-1]
        return ArrayType(parse_type(inner))
    elif type_str.startswith("Option<") and type_str.endswith(">"):
        inner = type_str[7:-1]
        return OptionType(parse_type(inner))
    return type_str
