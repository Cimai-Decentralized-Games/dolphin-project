import ast as py_ast
import textwrap
from typing import List, Optional, Dict, Any
import re
from .ir import (
    IRProgram, IRAccount, IRInstruction, IRField, 
    IRArgument, IRAccountUsage, IRStatement, IRRequire,
    IRExpression, IRLiteral, IRVariable, IRBinaryOp,
    SpanData, IRRequireData
)
from .core.types import SolanaType

class SolanaParser:
    VALID_TYPES = {'u8', 'u16', 'u32', 'u64', 'i8', 'i16', 'i32', 'i64', 
                   'bool', 'str', 'bytes', 'Pubkey', 'string'}  # Added 'string' as alias for 'str'

    def __init__(self, source_code: str):
        # Replace Vec<T> and Option<T> with temporary syntax for parsing
        source_code = textwrap.dedent(source_code).strip()
        source_code = re.sub(r'Vec<([^>]+)>', r'Vec_\1', source_code)
        source_code = re.sub(r'Option<([^>]+)>', r'Option_\1', source_code)
        self.source_code = source_code
        self.parsed_ast = py_ast.parse(self.source_code)
        self.current_program: Optional[IRProgram] = None
        self.processed_instructions: set = set()

    def parse(self) -> IRProgram:
        """Converts Python AST into Dolphin IR"""
        for node in self.parsed_ast.body:
            if isinstance(node, py_ast.ClassDef):
                self._parse_class(node)
        
        if not self.current_program:
            raise ValueError("No program definition found")
        
        return self.current_program

    def _parse_class(self, node: py_ast.ClassDef) -> None:
        """Parse class definitions which could be programs, accounts, or instructions"""
        decorators = self._get_decorators(node)
        
        if "program" in decorators:
            self._parse_program(node, decorators["program"])
            for item in node.body:
                if isinstance(item, py_ast.ClassDef):
                    nested_decorators = self._get_decorators(item)
                    if "account" in nested_decorators:
                        self._parse_account(item, nested_decorators["account"])
                elif isinstance(item, py_ast.FunctionDef):
                    if any(d.id == "instruction" for d in item.decorator_list 
                          if isinstance(d, py_ast.Name)):
                        self._parse_instruction(item)

    def _get_decorators(self, node: py_ast.AST) -> Dict[str, Any]:
        """Extract and parse decorators"""
        decorators = {}
        if hasattr(node, 'decorator_list'):
            for decorator in node.decorator_list:
                if isinstance(decorator, py_ast.Name):
                    decorators[decorator.id] = None
                elif isinstance(decorator, py_ast.Call):
                    if isinstance(decorator.func, py_ast.Name):
                        args = [self._parse_expression(arg) for arg in decorator.args]
                        kwargs = {
                            kw.arg: self._parse_expression(kw.value) 
                            for kw in decorator.keywords
                        }
                        decorators[decorator.func.id] = {
                            "args": args,
                            "kwargs": kwargs
                        }
        return decorators

    def _parse_program(self, node: py_ast.ClassDef, decorator_data: Dict) -> None:
        """Parse program class definition"""
        program_id = decorator_data["args"][0] if decorator_data and decorator_data["args"] else None
        
        self.current_program = IRProgram(
            name=node.name,
            program_id=program_id,
            version="0.1.0"
        )

    def _parse_account(self, node: py_ast.ClassDef, decorator_data: Dict) -> None:
        """Parse account class definition"""
        if not self.current_program:
            raise ValueError("Account must be defined within a program")

        account = IRAccount(name=node.name)
        
        # Parse PDA configuration if present
        if "pda" in self._get_decorators(node):
            pda_data = self._get_decorators(node)["pda"]
            if pda_data and pda_data["args"]:
                account.is_pda = True
                account.seeds = [
                    arg.data["value"] if isinstance(arg, IRLiteral) else str(arg)
                    for arg in pda_data["args"]
                ]
                account.discriminator = f"{account.name.lower()}_type"

        # Check for signer decorator
        is_signer = "signer" in self._get_decorators(node)

        # Parse fields
        for item in node.body:
            if isinstance(item, py_ast.AnnAssign):
                if isinstance(item.target, py_ast.Name):
                    type_name = self._get_type_name(item.annotation)
                    # Convert back Vec_T and Option_T to Vec<T> and Option<T>
                    if type_name.startswith('Vec_'):
                        type_name = f"Vec<{type_name[4:]}>"
                    elif type_name.startswith('Option_'):
                        type_name = f"Option<{type_name[7:]}>"
                    
                    # Validate type
                    base_type = type_name.split('<')[1].rstrip('>') if '<' in type_name else type_name
                    if base_type.lower() not in {t.lower() for t in self.VALID_TYPES}:
                        raise ValueError(f"Invalid type: {base_type}")
                    
                    field = IRField(
                        name=item.target.id,
                        type_name=type_name,
                        attributes=[]
                    )
                    account.fields.append(field)

        self.current_program.accounts.append(account)

    def _parse_instruction(self, node: py_ast.FunctionDef) -> None:
        """Parse instruction definition"""
        if not self.current_program:
            raise ValueError("Instruction must be defined within a program")

        instruction = IRInstruction(name=node.name)
        
        # Parse arguments (skip self)
        for arg in node.args.args[1:]:
            if hasattr(arg, 'annotation'):
                instruction.args.append(
                    IRArgument(
                        name=arg.arg,
                        type_name=self._get_type_name(arg.annotation)
                    )
                )

        # Parse accounts decorator if present
        for decorator in node.decorator_list:
            if (isinstance(decorator, py_ast.Call) and 
                isinstance(decorator.func, py_ast.Name) and 
                decorator.func.id == "accounts"):
                self._parse_accounts_decorator(decorator, instruction)

        # Parse body
        for stmt in node.body:
            parsed_stmt = self._parse_statement(stmt)
            if parsed_stmt:
                instruction.body.append(parsed_stmt)

        # Add signer validation if needed
        for account in instruction.accounts:
            if account.is_signer:
                require_data = IRRequireData(
                    condition=IRBinaryOp(
                        "==",
                        IRVariable(f"{account.name}.key()"),
                        IRVariable("signer.key()")
                    ),
                    message=f"{account.name} must be signer",
                    span=SpanData(0, 0)
                )
                instruction.body.insert(0, IRRequire(require_data))

        self.current_program.instructions.append(instruction)

    def _parse_accounts_decorator(self, node: py_ast.Call, instruction: IRInstruction) -> None:
        """Parse accounts decorator configuration"""
        for kw in node.keywords:
            account_type = self._get_type_name(kw.value)
            is_mutable = False
            is_signer = False

            if isinstance(kw.value, py_ast.Call):
                for attr in kw.value.keywords:
                    if attr.arg == "mutable":
                        is_mutable = attr.value.value
                    elif attr.arg == "signer":
                        is_signer = attr.value.value

            instruction.accounts.append(
                IRAccountUsage(
                    name=kw.arg,
                    account_type=account_type,
                    is_mutable=is_mutable,
                    is_signer=is_signer
                )
            )

    def _parse_statement(self, node: py_ast.AST) -> Optional[IRStatement]:
        """Parse instruction body statements"""
        if isinstance(node, py_ast.Assign):
            target = node.targets[0]
            if isinstance(target, py_ast.Name):
                target_name = target.id
            elif isinstance(target, py_ast.Attribute):
                if isinstance(target.value, py_ast.Attribute):
                    # Handle self.counter.authority
                    if isinstance(target.value.value, py_ast.Name) and target.value.value.id == 'self':
                        target_name = f"{target.value.attr}.{target.attr}"
                    else:
                        return None
                elif isinstance(target.value, py_ast.Name):
                    if target.value.id == 'self':
                        target_name = target.attr
                    else:
                        target_name = f"{target.value.id}.{target.attr}"
                else:
                    return None
            else:
                return None

            return IRStatement(
                kind="assignment",
                data={
                    "target": target_name,
                    "value": self._parse_expression(node.value)
                }
            )
        elif isinstance(node, py_ast.Assert):
            # Parse the assertion condition
            condition = self._parse_expression(node.test)
            # Check if this is a signer validation
            is_signer_check = (
                isinstance(condition, IRExpression) and
                condition.kind == "binary_op" and
                condition.data.get("op") == "==" and
                isinstance(condition.data.get("right"), dict) and
                condition.data.get("right", {}).get("data", {}).get("name") == "signer"
            )
            message = "signer validation required" if is_signer_check else "assertion failed"
            
            require_data = IRRequireData(
                condition=condition,
                message=message,
                span=SpanData(node.lineno, node.col_offset)
            )
            return IRRequire(require_data)
        elif isinstance(node, py_ast.Expr) and isinstance(node.value, py_ast.Call):
            if isinstance(node.value.func, py_ast.Name) and node.value.func.id == 'require':
                if len(node.value.args) != 2:
                    raise ValueError("require() must have exactly 2 arguments: condition and message")
                
                require_data = IRRequireData(
                    condition=self._parse_expression(node.value.args[0]),
                    message=(node.value.args[1].value 
                            if isinstance(node.value.args[1], py_ast.Constant)
                            else self._parse_expression(node.value.args[1])),
                    span=SpanData(node.lineno, node.col_offset)
                )
                return IRRequire(require_data)
            elif isinstance(node.value.func, py_ast.Attribute):
                return IRStatement(
                    kind="method_call",
                    data={
                        "target": self._parse_expression(node.value.func.value),
                        "method": node.value.func.attr,
                        "args": [self._parse_expression(arg) for arg in node.value.args]
                    }
                )
        return None

    def _parse_expression(self, node: py_ast.AST) -> IRExpression:
        """Parse expressions"""
        if isinstance(node, py_ast.Constant):
            return IRLiteral(node.value)
        elif isinstance(node, py_ast.Name):
            if node.id == 'signer':
                return IRVariable('signer')
            return IRVariable(node.id)
        elif isinstance(node, py_ast.Attribute):
            if isinstance(node.value, py_ast.Name):
                base_name = node.value.id
                if base_name == 'self' and node.attr == 'signer':
                    return IRVariable('signer')
                elif base_name == 'self':
                    return IRVariable(node.attr)
                elif base_name == 'signer':
                    return IRVariable(f"signer.{node.attr}")
                return IRVariable(f"{base_name}.{node.attr}")
            elif isinstance(node.value, py_ast.Attribute):
                if isinstance(node.value.value, py_ast.Name) and node.value.value.id == 'self':
                    return IRVariable(f"{node.value.attr}.{node.attr}")
        elif isinstance(node, py_ast.Compare):
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise ValueError("Only single comparisons are supported")
            
            return IRBinaryOp(
                self._get_compare_op_symbol(node.ops[0]),
                self._parse_expression(node.left),
                self._parse_expression(node.comparators[0])
            )
        
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")

    def _get_compare_op_symbol(self, op: py_ast.cmpop) -> str:
        """Convert Python AST comparison operators to string representation"""
        op_map = {
            py_ast.Eq: "==",
            py_ast.NotEq: "!=",
            py_ast.Lt: "<",
            py_ast.LtE: "<=",
            py_ast.Gt: ">",
            py_ast.GtE: ">=",
        }
        op_type = type(op)
        if op_type in op_map:
            return op_map[op_type]
        raise ValueError(f"Unsupported comparison operator: {op_type.__name__}")

    def _get_type_name(self, annotation: py_ast.AST) -> str:
        """Convert Python type annotations to Solana type names"""
        if isinstance(annotation, py_ast.Name):
            return annotation.id
        elif isinstance(annotation, py_ast.Subscript):
            if isinstance(annotation.value, py_ast.Name):
                container = annotation.value.id
                if container in ('List', 'Vec'):
                    element_type = self._get_type_name(annotation.slice)
                    return f"Vec_{element_type}"
                elif container == 'Option':
                    element_type = self._get_type_name(annotation.slice)
                    return f"Option_{element_type}"
        return "unknown"


