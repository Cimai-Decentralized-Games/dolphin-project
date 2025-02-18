from typing import List, Dict, Optional, Union, Any
from dataclasses import asdict, dataclass, field

@dataclass
class SpanData:
    """
    Represents source code location information.
    Maps to Rust's SpanData struct in compiler/ir.rs
    """
    line: int  # Maps to Rust's u32
    column: int  # Maps to Rust's u32

@dataclass
class IRNode:
    """Base class for all IR nodes"""
    name: str
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRProgram:
    """Top-level program IR node"""
    name: str
    program_id: str
    accounts: List['IRAccount'] = field(default_factory=list)
    instructions: List['IRInstruction'] = field(default_factory=list)
    types: List['IRCustomType'] = field(default_factory=list)
    version: str = field(default="0.1.0")
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRAccount:
    """Account structure IR node"""
    name: str
    fields: List['IRField'] = field(default_factory=list)
    is_program_owned: bool = field(default=True)
    is_pda: bool = field(default=False)
    seeds: List[str] = field(default_factory=list)
    discriminator: Optional[str] = field(default=None)
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRField:
    """Account field IR node"""
    name: str
    type_name: str
    attributes: List[str] = field(default_factory=list)
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRInstruction:
    """Instruction IR node"""
    name: str
    args: List['IRArgument'] = field(default_factory=list)
    accounts: List['IRAccountUsage'] = field(default_factory=list)
    body: List['IRStatement'] = field(default_factory=list)
    return_type: Optional[str] = field(default=None)
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRArgument:
    """Instruction argument IR node"""
    name: str
    type_name: str
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRAccountUsage:
    """Account usage in instruction context"""
    name: str
    account_type: str
    is_mutable: bool = field(default=False)
    is_signer: bool = field(default=False)
    is_optional: bool = field(default=False)
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRStatement:
    """Base class for instruction statements"""
    kind: str
    data: Dict[str, Any]
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRAssignment(IRStatement):
    def __init__(self, target: str, value: 'IRExpression', span: Optional[SpanData] = None):
        super().__init__(
            kind="assignment",
            data={"target": target, "value": to_json(value)},
            span=span
        )

@dataclass
class IRMethodCall(IRStatement):
    """Method call statement"""
    def __init__(self, target: str, method: str, args: List['IRExpression'], 
                 span: Optional[SpanData] = None):
        super().__init__(
            kind="method_call",
            data={
                "target": target,
                "method": method,
                "args": args
            },
            span=span
        )

@dataclass
class IRRequireData:
    """Represents the data structure of a `require` statement"""
    condition: 'IRExpression'
    message: str
    span: SpanData

@dataclass
class IRRequire(IRStatement):
    """Require statement"""
    def __init__(self, data: IRRequireData, span: Optional[SpanData] = None):
        super().__init__(
            kind="require",
            data=asdict(data),  # Convert IRRequireData to a dictionary
            span=span
        )

@dataclass
class IRExpression:
    """Base class for expressions"""
    kind: str
    data: Dict[str, Any]
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRLiteral(IRExpression):
    """Literal value expression"""
    def __init__(self, value: Union[int, float, str, bool], span: Optional[SpanData] = None):
        super().__init__(
            kind="literal",
            data={"value": value},
            span=span
        )

@dataclass
class IRVariable(IRExpression):
    """Variable reference expression"""
    def __init__(self, name: str, span: Optional[SpanData] = None):
        super().__init__(
            kind="variable",
            data={"name": name},
            span=span
        )

@dataclass
class IRBinaryOp(IRExpression):
    """Binary operation expression"""
    def __init__(self, op: str, left: 'IRExpression', right: 'IRExpression', 
                 span: Optional[SpanData] = None):
        super().__init__(
            kind="binary_op",
            data={
                "op": op,
                "left": to_json(left),
                "right": to_json(right)
            },
            span=span
        )

@dataclass
class IRCustomType:
    """Custom type definition"""
    name: str
    variants: List[str] = field(default_factory=list)
    fields: List[IRField] = field(default_factory=list)
    span: Optional[SpanData] = field(default=None)

def to_json(node: Union[IRNode, IRProgram, IRAccount, IRField, IRInstruction,
                        IRArgument, IRAccountUsage, IRStatement, IRExpression,
                        IRCustomType, IRRequire, SpanData, None]) -> Dict[str, Any]:
    """Convert IR node to JSON-serializable dictionary"""
    if isinstance(node, SpanData):
        return {
            "line": node.line,
            "column": node.column
        }
    elif isinstance(node, IRProgram):
        return {
            "program_name": node.name,
            "program_id": node.program_id.data["value"] if isinstance(node.program_id, IRLiteral) else str(node.program_id),
            "program_version": node.version,
            "instructions": [to_json(instr) for instr in node.instructions],
            "accounts": [to_json(account) for account in node.accounts],
            "types": [to_json(type_) for type_ in node.types]
        }
    elif isinstance(node, IRAccount):
        return {
            "name": node.name,
            "fields": [to_json(field) for field in node.fields],
            "is_program_owned": node.is_program_owned,
            "is_pda": node.is_pda,
            "seeds": [to_json(seed) for seed in node.seeds],
            "discriminator": node.discriminator
        }
    elif isinstance(node, IRField):
        return {
            "name": node.name,
            "ty": node.type_name,
            "attributes": node.attributes
        }
    elif isinstance(node, IRInstruction):
        return {
            "name": node.name,
            "arguments": [to_json(arg) for arg in node.args],
            "accounts": [
                to_json(IRAccountUsage(name=acc, account_type="Account")) for acc in node.accounts
            ] if node.accounts else [],
            "body": [to_json(stmt) for stmt in node.body]
        }
    elif isinstance(node, IRArgument):
        return {
            "name": node.name,
            "ty": node.type_name
        }
    elif isinstance(node, IRAccountUsage):
        return {
            "name": node.name,
            "account_type": node.account_type,
            "is_mutable": node.is_mutable,
            "is_signer": node.is_signer
        }
    elif isinstance(node, IRStatement):
        return {
            "kind": node.kind,
            "data": to_json(node.data) if isinstance(node.data, dict) else node.data,
            "span": to_json(node.span) if node.span else None
        }
    elif isinstance(node, IRRequireData):
        return {
            "condition": to_json(node.condition),
            "message": node.message,
            "span": to_json(node.span)
        }
    elif isinstance(node, IRRequire):
        return {
            "kind": "require",
            "data": to_json(node.data)  # Directly serialize the data
        }
    elif isinstance(node, IRExpression):
        return {
            "kind": node.kind,
            "data": to_json(node.data) if isinstance(node.data, dict) else node.data,
            "span": to_json(node.span) if node.span else None
        }
    elif isinstance(node, IRLiteral):
        return node.data["value"]
    elif isinstance(node, (list, tuple)):
        return [to_json(x) for x in node]
    elif isinstance(node, dict):
        return {k: to_json(v) for k, v in node.items()}
    elif isinstance(node, (str, int, float, bool)) or node is None:
        return node
    else:
        raise ValueError(f"Unsupported type for JSON conversion: {type(node)}")

def from_json(data: Dict[str, Any]) -> Union[IRNode, IRProgram, IRAccount, IRField, 
                                            IRInstruction, IRArgument, IRAccountUsage, 
                                            IRStatement, IRExpression, IRCustomType, 
                                            IRRequire, SpanData]:
    """Create IR node from JSON-serializable dictionary"""
    if not isinstance(data, dict):
        return data
    
    node_type = data.pop("type", None)
    if node_type is None:
        return data
    
    # Handle span data
    if all(key in data for key in ["line", "column"]):
        return SpanData(
            line=data["line"],
            column=data["column"]
        )

    # Handle IRRequire
    if "kind" in data and data["kind"] == "require":
        require_data = data["data"]["data"]
        return IRRequire(
            data=IRRequireData(
                condition=from_json(require_data["condition"]),
                message=require_data["message"],
                span=from_json(require_data["span"]) if "span" in require_data else None
            )
        )
    
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
