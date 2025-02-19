from typing import List, Dict, Optional, Union, Any
from dataclasses import asdict, dataclass, field

@dataclass
class SpanData:
    """Maps to Rust's SpanData struct"""
    start: int = 0  # Maps to Rust's usize
    end: int = 0    # Maps to Rust's usize
    line: int = 0   # Maps to Rust's usize
    column: int = 0 # Maps to Rust's usize

@dataclass
class Span:
    """Maps to Rust's Span struct"""
    start: int  # Maps to Rust's usize
    end: int  # Maps to Rust's usize
    line: int  # Maps to Rust's usize
    column: int  # Maps to Rust's usize

@dataclass
class IRExpression:
    """Base class for expressions"""
    kind: str  # One of: "Literal", "Variable", "BinaryOp"
    data: Dict[str, Any]
    span: Optional[Span] = field(default_factory=lambda: Span(0, 0, 0, 0))

@dataclass
class IRLiteral(IRExpression):
    """Literal value expression"""
    def __init__(self, value: Union[int, float, str, bool], span: Optional[Span] = None):
        super().__init__(
            kind="Literal",  # Maps to Rust's ExpressionKind::Literal
            data={"value": value},  # The value will be wrapped in "Literal" during serialization
            span=span or Span(0, 0, 0, 0)
        )

@dataclass
class IRVariable(IRExpression):
    """Variable reference expression"""
    def __init__(self, name: str, span: Optional[Span] = None):
        super().__init__(
            kind="Variable",  # Maps to Rust's ExpressionKind::Variable
            data={"name": name},  # The name will be wrapped in "Variable" during serialization
            span=span or Span(0, 0, 0, 0)
        )

@dataclass
class IRList(IRExpression):
    """List expression"""
    def __init__(self, elements: List[IRExpression], span: Optional[Span] = None):
        super().__init__(
            kind="List",  # Maps to Rust's ExpressionKind::List
            data={"elements": elements},
            span=span or Span(0, 0, 0, 0)
        )

@dataclass
class IRBinaryOp(IRExpression):
    """Binary operation expression"""
    def __init__(self, op: str, left: 'IRExpression', right: 'IRExpression', 
                 span: Optional[Span] = None):
        # Create a proper Expression structure for each operand
        left_expr = {
            "kind": {
                left.kind: left.data.get("value", left.data.get("name", ""))
            },
            "span": to_json(left.span)
        } if isinstance(left, IRExpression) else to_json(left)
        
        right_expr = {
            "kind": {
                right.kind: right.data.get("value", right.data.get("name", ""))
            },
            "span": to_json(right.span)
        } if isinstance(right, IRExpression) else to_json(right)
        
        super().__init__(
            kind="BinaryOp",  # Maps to Rust's ExpressionKind::BinaryOp
            data={
                "op": op,
                "left": left_expr,
                "right": right_expr
            },
            span=span or Span(0, 0, 0, 0)
        )

@dataclass
class IRRequireData:
    """Maps to Rust's RequireData struct"""
    condition: IRExpression
    message: str
    span: SpanData

@dataclass
class IRStatement:
    """Maps to Rust's Statement struct"""
    kind: str  # One of: "Assignment", "MethodCall", "Require"
    data: Dict[str, Any]
    span: Span = field(default_factory=lambda: Span(0, 0, 0, 0))

@dataclass
class IRAssignment(IRStatement):
    """Maps to Rust's Assignment variant of StatementKind"""
    def __init__(self, target: str, value: IRExpression, span: Optional[Span] = None):
        super().__init__(
            kind="Assignment",  # PascalCase to match Rust enum
            data={
                "target": target,
                "value": to_json(value)
            },
            span=span or Span(0, 0, 0, 0)
        )

@dataclass
class IRMethodCall(IRStatement):
    """Maps to Rust's MethodCall variant of StatementKind"""
    def __init__(self, target: str, method: str, args: List[IRExpression], 
                 span: Optional[Span] = None):
        super().__init__(
            kind="MethodCall",  # PascalCase to match Rust enum
            data={
                "target": target,
                "method": method,
                "args": args
            },
            span=span or Span(0, 0, 0, 0)
        )

@dataclass
class IRRequire(IRStatement):
    """Maps to Rust's Require variant of StatementKind"""
    def __init__(self, data: Union[IRRequireData, Dict], span: Optional[Span] = None):
        # Handle both IRRequireData and dict inputs
        if isinstance(data, dict):
            require_data = data
        else:
            require_data = {
                "condition": {
                    "kind": {
                        "Literal": {
                            "Boolean": True
                        }
                    },
                    "span": asdict(data.span) if data.span else {"start": 0, "end": 0, "line": 0, "column": 0}
                },
                "message": data.message,
                "span": asdict(data.span) if data.span else {"line": 0, "column": 0}
            }
        
        super().__init__(
            kind="Require",  # PascalCase to match Rust enum
            data={"data": require_data},
            span=span or Span(0, 0, 0, 0)
        )

@dataclass
class IRField:
    """Maps to Rust's AccountField struct"""
    name: str
    type_name: str
    attributes: List[str] = field(default_factory=list)
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRAccountUsage:
    """Maps to Rust's AccountUsage struct"""
    name: str
    account_type: str
    is_mutable: bool = False
    is_signer: bool = False
    is_optional: bool = False
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRArgument:
    """Maps to Rust's InstructionArgument struct"""
    name: str
    type_name: str
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRAccount:
    """Maps to Rust's Account struct"""
    name: str
    fields: List[IRField] = field(default_factory=list)
    is_program_owned: bool = True
    is_pda: bool = False
    seeds: List[str] = field(default_factory=list)
    discriminator: Optional[str] = None
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRInstruction:
    """Maps to Rust's Instruction struct"""
    name: str
    args: List[IRArgument] = field(default_factory=list)
    accounts: List[IRAccountUsage] = field(default_factory=list)
    body: List[IRStatement] = field(default_factory=list)
    return_type: Optional[str] = field(default=None)
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRCustomType:
    """Maps to Rust's CustomType struct"""
    name: str
    variants: List[str] = field(default_factory=list)
    fields: List[IRField] = field(default_factory=list)
    span: Optional[SpanData] = field(default=None)

@dataclass
class IRProgram:
    """Maps to Rust's IR struct"""
    name: str
    program_id: str
    accounts: List[IRAccount] = field(default_factory=list)
    instructions: List[IRInstruction] = field(default_factory=list)
    types: List[IRCustomType] = field(default_factory=list)
    version: str = field(default="0.1.0")
    span: Optional[SpanData] = field(default=None)

def to_json(node: Union[IRProgram, IRAccount, IRField, IRInstruction,
                       IRArgument, IRAccountUsage, IRStatement, IRExpression,
                       IRCustomType, IRRequireData, SpanData, Span, None]) -> Dict[str, Any]:
    """Convert IR node to JSON-serializable dictionary that matches Rust's format"""
    if isinstance(node, (SpanData, Span)):
        # Ensure all span fields are present
        return {
            "start": getattr(node, "start", 0),
            "end": getattr(node, "end", 0),
            "line": getattr(node, "line", 0),
            "column": getattr(node, "column", 0)
        }
    
    elif isinstance(node, IRExpression):
        # Create an Expression structure that matches Rust's format
        result = {"span": to_json(node.span)}
        
        if isinstance(node, IRLiteral):
            # Create a Literal variant with the appropriate inner value
            value = node.data["value"]
            inner_value = None
            if isinstance(value, bool):
                inner_value = {"Boolean": value}
            elif isinstance(value, int):
                inner_value = {"Integer": value}
            elif isinstance(value, float):
                inner_value = {"Float": value}
            elif isinstance(value, str):
                inner_value = {"String": value}
            elif value is None:
                inner_value = {"Integer": 0}  # Default to Integer(0) for null values
            
            result["kind"] = {"Literal": inner_value}
        elif isinstance(node, IRVariable):
            result["kind"] = {"Variable": node.data["name"]}
        elif isinstance(node, IRList):
            result["kind"] = {
                "List": [to_json(element) for element in node.data["elements"]]
            }
        elif isinstance(node, IRBinaryOp):
            # Ensure BinaryOp matches Rust's expected format
            result["kind"] = {
                "BinaryOp": {
                    "op": node.data["op"],
                    "left": {
                        "kind": node.data["left"]["kind"],
                        "span": node.data["left"]["span"]
                    },
                    "right": {
                        "kind": node.data["right"]["kind"],
                        "span": node.data["right"]["span"]
                    }
                }
            }
        return result
    
    elif isinstance(node, IRStatement):
        if node.kind == "Assignment":
            return {
                "kind": {
                    "Assignment": {
                        "target": node.data["target"],
                        "value": to_json(node.data["value"])
                    }
                },
                "span": to_json(node.span)
            }
        elif node.kind == "MethodCall":
            return {
                "kind": {
                    "MethodCall": {
                        "target": node.data["target"],
                        "method": node.data["method"],
                        "args": [to_json(arg) for arg in node.data["args"]]
                    }
                },
                "span": to_json(node.span)
            }
        elif node.kind == "Require":
            # Convert IRRequireData to match Rust's RequireData struct
            require_data = node.data["data"]
            if not isinstance(require_data, dict):
                require_data = asdict(require_data)
            
            # Create the Require statement that matches Rust's format
            return {
                "kind": {
                    "Require": {
                        "data": {  # Wrap in data field to match Rust struct
                            "condition": to_json(require_data["condition"]),
                            "message": require_data["message"],
                            "span": to_json(require_data["span"])
                        }
                    }
                },
                "span": to_json(node.span)
            }
    
    elif isinstance(node, IRProgram):
        return {
            "program_name": node.name,
            "program_id": node.program_id,
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
            "seeds": node.seeds,
            "discriminator": node.discriminator
        }
    
    elif isinstance(node, IRField):
        return {
            "name": node.name,
            "ty": node.type_name,  # Maps to Rust's ty field
            "attributes": node.attributes
        }
    
    elif isinstance(node, IRArgument):
        return {
            "name": node.name,
            "ty": node.type_name  # Maps to Rust's ty field
        }
    
    elif isinstance(node, IRAccountUsage):
        return {
            "name": node.name,
            "account_type": node.account_type,
            "is_mutable": node.is_mutable,
            "is_signer": node.is_signer,
            "is_optional": node.is_optional
        }
    
    elif isinstance(node, IRInstruction):
        return {
            "name": node.name,
            "arguments": [to_json(arg) for arg in node.args],
            "accounts": [to_json(acc) for acc in node.accounts],
            "body": [to_json(stmt) for stmt in node.body]
        }
    
    elif isinstance(node, (list, tuple)):
        return [to_json(x) for x in node]
    elif isinstance(node, dict):
        return {k: to_json(v) for k, v in node.items()}
    elif isinstance(node, (str, int, float, bool)) or node is None:
        return node
    
    return asdict(node)

def from_json(data: Dict[str, Any]) -> Union[IRProgram, IRAccount, IRField, IRInstruction,
                                            IRArgument, IRAccountUsage, IRStatement, IRExpression,
                                            IRCustomType, IRRequireData, SpanData, Span]:
    """Create IR node from JSON-serializable dictionary"""
    if not isinstance(data, dict):
        return data
    
    if "kind" in data:
        kind_data = next(iter(data["kind"].items()))
        kind_name = kind_data[0]
        kind_value = kind_data[1]
        
        span = from_json(data.get("span"))
        
        # Handle all expression types
        if kind_name == "Literal":
            # Extract the inner literal value
            inner_kind, inner_value = next(iter(kind_value.items()))
            # Convert to appropriate Python type
            if inner_kind == "Integer":
                value = int(inner_value)
            elif inner_kind == "Float":
                value = float(inner_value)
            elif inner_kind == "String":
                value = str(inner_value)
            elif inner_kind == "Boolean":
                value = bool(inner_value)
            else:
                raise ValueError(f"Unknown literal type: {inner_kind}")
            return IRLiteral(value=value, span=span)
        elif kind_name == "Variable":
            return IRVariable(name=kind_value, span=span)
        elif kind_name == "List":
            return IRList(
                elements=[from_json(element) for element in kind_value],
                span=span
            )
        elif kind_name == "BinaryOp":
            # Ensure nested expressions are properly handled
            left_expr = {"kind": kind_value["left"]["kind"], "span": kind_value["left"]["span"]}
            right_expr = {"kind": kind_value["right"]["kind"], "span": kind_value["right"]["span"]}
            return IRBinaryOp(
                op=kind_value["op"],
                left=from_json(left_expr),
                right=from_json(right_expr),
                span=span
            )
        elif kind_name == "Assignment":
            return IRAssignment(
                target=kind_value["target"],
                value=from_json(kind_value["value"]),
                span=from_json(data["span"])
            )
        elif kind_name == "MethodCall":
            return IRMethodCall(
                target=kind_value["target"],
                method=kind_value["method"],
                args=[from_json(arg) for arg in kind_value["args"]],
                span=from_json(data["span"])
            )
        elif kind_name == "Require":
            require_data = kind_value["data"]  # Extract the nested data field
            return IRRequire(
                data=IRRequireData(
                    condition=from_json(require_data["condition"]),
                    message=require_data["message"],
                    span=from_json(require_data["span"])
                ),
                span=from_json(data["span"])
            )
    
    # Handle remaining types...
    if "program_name" in data:
        return IRProgram(
            name=data["program_name"],
            program_id=data["program_id"],
            version=data.get("program_version", "0.1.0"),
            instructions=[from_json(i) for i in data.get("instructions", [])],
            accounts=[from_json(a) for a in data.get("accounts", [])],
            types=[from_json(t) for t in data.get("types", [])]
        )
    elif "name" in data:
        if "fields" in data:  # Account
            return IRAccount(
                name=data["name"],
                fields=[from_json(field) for field in data["fields"]],
                is_program_owned=data.get("is_program_owned", True),
                is_pda=data.get("is_pda", False),
                seeds=data.get("seeds", []),
                discriminator=data.get("discriminator")
            )
        elif "ty" in data:  # AccountField or InstructionArgument
            if "attributes" in data:  # AccountField
                return IRField(
                    name=data["name"],
                    type_name=data["ty"],  # Convert from Rust's ty to Python's type_name
                    attributes=data.get("attributes", [])
                )
            else:  # InstructionArgument
                return IRArgument(
                    name=data["name"],
                    type_name=data["ty"]  # Convert from Rust's ty to Python's type_name
                )
        elif "variants" in data:  # CustomType
            return IRCustomType(
                name=data["name"],
                variants=data["variants"]
            )
        elif "arguments" in data:  # Instruction
            return IRInstruction(
                name=data["name"],
                args=[from_json(arg) for arg in data["arguments"]],
                accounts=[from_json(acc) for acc in data.get("accounts", [])],
                body=[from_json(stmt) for stmt in data.get("body", [])]
            )
        elif "account_type" in data:  # AccountUsage
            return IRAccountUsage(
                name=data["name"],
                account_type=data["account_type"],
                is_mutable=data.get("is_mutable", False),
                is_signer=data.get("is_signer", False)
            )
    
    return data