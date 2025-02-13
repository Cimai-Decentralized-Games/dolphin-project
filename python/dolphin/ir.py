from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass, field

@dataclass
class IRNode:
    """Base class for all IR nodes"""
    span: Optional[Dict[str, int]] = None  # Source code location information

@dataclass
class IRProgram(IRNode):
    """Top-level program IR node"""
    name: str
    program_id: str
    version: str = "0.1.0"
    accounts: List['IRAccount'] = field(default_factory=list)
    instructions: List['IRInstruction'] = field(default_factory=list)
    types: List['IRCustomType'] = field(default_factory=list)

@dataclass
class IRAccount(IRNode):
    """Account structure IR node"""
    name: str
    fields: List['IRField'] = field(default_factory=list)
    is_program_owned: bool = True
    is_pda: bool = False
    seeds: List[str] = field(default_factory=list)
    discriminator: Optional[str] = None

@dataclass
class IRField(IRNode):
    """Account field IR node"""
    name: str
    type_name: str
    attributes: List[str] = field(default_factory=list)

@dataclass
class IRInstruction(IRNode):
    """Instruction IR node"""
    name: str
    args: List['IRArgument'] = field(default_factory=list)
    accounts: List['IRAccountUsage'] = field(default_factory=list)
    body: List['IRStatement'] = field(default_factory=list)
    return_type: Optional[str] = None

@dataclass
class IRArgument(IRNode):
    """Instruction argument IR node"""
    name: str
    type_name: str

@dataclass
class IRAccountUsage(IRNode):
    """Account usage in instruction context"""
    name: str
    account_type: str
    is_mutable: bool = False
    is_signer: bool = False
    is_optional: bool = False

@dataclass
class IRStatement(IRNode):
    """Base class for instruction statements"""
    kind: str
    data: Dict[str, Any]

@dataclass
class IRAssignment(IRStatement):
    """Assignment statement"""
    def __init__(self, target: str, value: 'IRExpression'):
        super().__init__(
            kind="assignment",
            data={"target": target, "value": value}
        )

@dataclass
class IRMethodCall(IRStatement):
    """Method call statement"""
    def __init__(self, target: str, method: str, args: List['IRExpression']):
        super().__init__(
            kind="method_call",
            data={
                "target": target,
                "method": method,
                "args": args
            }
        )

@dataclass
class IRExpression(IRNode):
    """Base class for expressions"""
    kind: str
    data: Dict[str, Any]

@dataclass
class IRLiteral(IRExpression):
    """Literal value expression"""
    def __init__(self, value: Union[int, float, str, bool]):
        super().__init__(
            kind="literal",
            data={"value": value}
        )

@dataclass
class IRVariable(IRExpression):
    """Variable reference expression"""
    def __init__(self, name: str):
        super().__init__(
            kind="variable",
            data={"name": name}
        )

@dataclass
class IRBinaryOp(IRExpression):
    """Binary operation expression"""
    def __init__(self, op: str, left: 'IRExpression', right: 'IRExpression'):
        super().__init__(
            kind="binary_op",
            data={
                "op": op,
                "left": left,
                "right": right
            }
        )

@dataclass
class IRCustomType(IRNode):
    """Custom type definition"""
    name: str
    variants: List[str] = field(default_factory=list)
    fields: List[IRField] = field(default_factory=list)

def to_json(node: IRNode) -> Dict[str, Any]:
    """Convert IR node to JSON-serializable dictionary"""
    if isinstance(node, (list, tuple)):
        return [to_json(x) for x in node]
    elif isinstance(node, IRNode):
        result = {"type": node.__class__.__name__}
        for field, value in node.__dict__.items():
            if field != "span":  # Skip span information in JSON
                result[field] = to_json(value)
        return result
    elif isinstance(node, (str, int, float, bool)):
        return node
    elif isinstance(node, dict):
        return {k: to_json(v) for k, v in node.items()}
    elif node is None:
        return None
    else:
        raise ValueError(f"Unsupported type for JSON conversion: {type(node)}")

def from_json(data: Dict[str, Any]) -> IRNode:
    """Create IR node from JSON-serializable dictionary"""
    if not isinstance(data, dict):
        return data
    
    node_type = data.pop("type", None)
    if node_type is None:
        return data
    
    cls = globals().get(node_type)
    if cls is None:
        raise ValueError(f"Unknown IR node type: {node_type}")
    
    # Recursively convert nested structures
    for key, value in data.items():
        if isinstance(value, dict):
            data[key] = from_json(value)
        elif isinstance(value, list):
            data[key] = [from_json(x) if isinstance(x, dict) else x for x in value]
    
    return cls(**data)
