import ast as py_ast
from typing import List, Optional, Dict, Any
from .ast import Node
from .ir import (
    IRProgram, IRAccount, IRInstruction, IRField, 
    IRArgument, IRAccountUsage, IRStatement,
    IRExpression, IRLiteral, IRVariable, IRBinaryOp
)

class SolanaParser:
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.parsed_ast = py_ast.parse(source_code)
        self.current_program: Optional[IRProgram] = None
        self.current_account: Optional[IRAccount] = None
        self.current_instruction: Optional[IRInstruction] = None

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
        elif "account" in decorators:
            self._parse_account(node, decorators["account"])
        elif "instruction" in decorators:
            self._parse_instruction(node, decorators["instruction"])

    def _get_decorators(self, node: py_ast.ClassDef) -> Dict[str, Any]:
        """Extract and parse decorators"""
        decorators = {}
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
                account.seeds = pda_data["args"]

        # Parse fields
        for item in node.body:
            if isinstance(item, py_ast.AnnAssign):
                field = self._parse_field(item)
                account.fields.append(field)

        self.current_program.accounts.append(account)

    def _parse_instruction(self, node: py_ast.ClassDef, decorator_data: Dict) -> None:
        """Parse instruction class definition"""
        if not self.current_program:
            raise ValueError("Instruction must be defined within a program")

        instruction = IRInstruction(name=node.name)

        # Parse instruction methods
        for item in node.body:
            if isinstance(item, py_ast.FunctionDef):
                if item.name == "execute":
                    self._parse_instruction_execute(item, instruction)

        self.current_program.instructions.append(instruction)

    def _parse_field(self, node: py_ast.AnnAssign) -> IRField:
        """Parse account field definition"""
        name = node.target.id
        type_name = self._get_type_name(node.annotation)
        attributes = []

        # Parse field decorators if any
        if hasattr(node, 'decorator_list'):
            for decorator in node.decorator_list:
                if isinstance(decorator, py_ast.Name):
                    attributes.append(decorator.id)

        return IRField(name=name, type_name=type_name, attributes=attributes)

    def _parse_instruction_execute(self, node: py_ast.FunctionDef, instruction: IRInstruction) -> None:
        """Parse instruction execute method"""
        # Parse arguments
        for arg in node.args.args[1:]:  # Skip 'self'
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
        instruction.body = [self._parse_statement(stmt) for stmt in node.body]

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

    def _parse_statement(self, node: py_ast.AST) -> IRStatement:
        """Parse instruction body statements"""
        if isinstance(node, py_ast.Assign):
            return IRStatement(
                kind="assignment",
                data={
                    "target": node.targets[0].id,
                    "value": self._parse_expression(node.value)
                }
            )
        elif isinstance(node, py_ast.Expr):
            if isinstance(node.value, py_ast.Call):
                return IRStatement(
                    kind="method_call",
                    data={
                        "target": self._parse_expression(node.value.func),
                        "args": [self._parse_expression(arg) for arg in node.value.args]
                    }
                )
        raise ValueError(f"Unsupported statement type: {type(node).__name__}")

    def _parse_expression(self, node: py_ast.AST) -> IRExpression:
        """Parse expressions"""
        if isinstance(node, py_ast.Constant):
            return IRLiteral(node.value)
        elif isinstance(node, py_ast.Name):
            return IRVariable(node.id)
        elif isinstance(node, py_ast.BinOp):
            return IRBinaryOp(
                self._get_op_symbol(node.op),
                self._parse_expression(node.left),
                self._parse_expression(node.right)
            )
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")

    def _get_op_symbol(self, op: py_ast.operator) -> str:
        """Convert Python AST operators to string representation"""
        op_map = {
            py_ast.Add: "+",
            py_ast.Sub: "-",
            py_ast.Mult: "*",
            py_ast.Div: "/",
            py_ast.Mod: "%",
            py_ast.BitAnd: "&",
            py_ast.BitOr: "|",
            py_ast.BitXor: "^",
        }
        op_type = type(op)
        if op_type in op_map:
            return op_map[op_type]
        raise ValueError(f"Unsupported operator: {op_type.__name__}")

    def _get_type_name(self, annotation: py_ast.AST) -> str:
        """Convert Python type annotations to Solana type names"""
        if isinstance(annotation, py_ast.Name):
            return annotation.id
        elif isinstance(annotation, py_ast.Subscript):
            # Handle generic types like List[int]
            container = annotation.value.id
            if container == "List":
                element_type = self._get_type_name(annotation.slice)
                return f"Vec<{element_type}>"
        return "unknown"
