# python/dolphin/ir_gen.py
import ast
from typing import List, Optional, Dict, Any
from .core.types import (
    AccountDefinition, 
    AccountField, 
    InstructionDefinition,
    InstructionArgument,
    InstructionAccount,
    SolanaType
)
from .ast import Node, parse_file
from dolphin.generator.accounts import AccountDefinition as AccountDefinitionGenerator
from dolphin.generator.instructions import InstructionDefinition as InstructionDefinitionGenerator

class IRGenerator(ast.NodeVisitor):
    def __init__(self):
        self.accounts: List[AccountDefinition] = []
        self.instructions: List[InstructionDefinition] = []
        self.current_scope: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef):
        """Process class definitions which could be accounts or instructions."""
        decorators = [d for d in node.decorator_list if isinstance(d, ast.Name)]
        decorator_names = {d.id for d in decorators}

        if "account" in decorator_names:
            self._process_account(node)
        elif "instruction" in decorator_names:
            self._process_instruction(node)

    def _process_account(self, node: ast.ClassDef):
        """Convert a Python class with @account decorator to an AccountDefinition."""
        account = AccountDefinition(
            name=node.name,
            fields=[],
            is_pda=False,
            seeds=[]
        )
        
        # Process PDA decorator if present
        for decorator in node.decorator_list:
            if (isinstance(decorator, ast.Call) and 
                isinstance(decorator.func, ast.Name) and 
                decorator.func.id == "pda"):
                seeds = [
                    arg.s for arg in decorator.args 
                    if isinstance(arg, ast.Str)
                ]
                account.set_pda(seeds)

        # Process class body for fields
        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                field_name = item.target.id
                field_type = self._get_type_annotation(item.annotation)
                
                # Get field attributes from decorators if any
                attributes = []
                if hasattr(item, 'decorator_list'):
                    for decorator in item.decorator_list:
                        if isinstance(decorator, ast.Name):
                            attributes.append(decorator.id)
                
                account.add_field(field_name, field_type, attributes)

        self.accounts.append(account)

    def _process_instruction(self, node: ast.ClassDef):
        """Convert a Python class with @instruction decorator to an InstructionDefinition."""
        instruction = InstructionDefinition(
            name=node.name,
            arguments=[],
            accounts=[],
            body=[]
        )
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "execute":
                # Process arguments
                for arg in item.args.args:
                    if arg.name != "self":
                        arg_type = self._get_type_annotation(arg.annotation)
                        instruction.add_argument(arg.name, arg_type)
                
                # Process accounts from context
                for decorator in item.decorator_list:
                    if (isinstance(decorator, ast.Call) and 
                        isinstance(decorator.func, ast.Name) and 
                        decorator.func.id == "accounts"):
                        self._process_instruction_accounts(decorator, instruction)
                
                # Process instruction body
                instruction.body = self._process_instruction_body(item.body)

        self.instructions.append(instruction)

    def _process_instruction_accounts(self, decorator: ast.Call, instruction: InstructionDefinition):
        """Process accounts decorator for instruction context."""
        for kw in decorator.keywords:
            account_type = self._get_type_annotation(kw.value)
            is_mutable = False
            is_signer = False
            
            # Check for account attributes in decorator
            if isinstance(kw.value, ast.Call):
                for attr in kw.value.keywords:
                    if attr.arg == "mutable":
                        is_mutable = attr.value.value
                    elif attr.arg == "signer":
                        is_signer = attr.value.value
            
            instruction.add_account(kw.arg, account_type, is_mutable, is_signer)

    def _get_type_annotation(self, annotation: ast.AST) -> str:
        """Convert Python type annotations to Solana types."""
        if isinstance(annotation, ast.Name):
            return SolanaType.from_python_type(annotation.id)
        elif isinstance(annotation, ast.Subscript):
            value_type = self._get_type_annotation(annotation.slice.value)
            return f"Vec<{value_type}>"
        return "unknown"

    def _process_instruction_body(self, body: List[ast.AST]) -> List[Dict[str, Any]]:
        """Convert Python instruction body to IR representation."""
        statements = []
        for node in body:
            if isinstance(node, ast.Assign):
                statements.append({
                    "type": "assignment",
                    "target": self._process_expression(node.targets[0]),
                    "value": self._process_expression(node.value)
                })
            elif isinstance(node, ast.Expr):
                if isinstance(node.value, ast.Call):
                    statements.append({
                        "type": "call",
                        "value": self._process_expression(node.value)
                    })
        return statements

    def _process_expression(self, node: ast.AST) -> Dict[str, Any]:
        """Convert Python expressions to IR representation."""
        if isinstance(node, ast.Name):
            return {"type": "variable", "name": node.id}
        elif isinstance(node, ast.Num):
            return {"type": "literal", "value": node.n}
        elif isinstance(node, ast.Str):
            return {"type": "literal", "value": node.s}
        elif isinstance(node, ast.Call):
            return {
                "type": "call",
                "function": self._process_expression(node.func),
                "args": [self._process_expression(arg) for arg in node.args]
            }
        elif isinstance(node, ast.Attribute):
            return {
                "type": "attribute",
                "value": self._process_expression(node.value),
                "attr": node.attr
            }
        return {"type": "unknown"}

    def generate(self, source_code: str) -> Dict[str, Any]:
        """Generate IR from source code."""
        tree = ast.parse(source_code)
        self.visit(tree)
        
        return {
            "accounts": [account.to_ir() for account in self.accounts],
            "instructions": [instruction.to_ir() for instruction in self.instructions]
        }

def generate_ir(source_code: str) -> Dict[str, Any]:
    """Convenience function to generate IR from source code."""
    generator = IRGenerator()
    return generator.generate(source_code)

if __name__ == "__main__":
    # Example usage
    sample_code = """
    @account
    @pda("mint", "owner")
    class TokenAccount:
        mint: Pubkey
        owner: Pubkey
        amount: int

    @instruction
    class Transfer:
        def execute(self, amount: int):
            self.token_account.amount -= amount
    """
    
    ir = generate_ir(sample_code)
    
    # Print generated IR
    for account in ir["accounts"]:
        print(f"Account: {account.name}")
        print(account.generate_code())
    
    for instruction in ir["instructions"]:
        print(f"Instruction: {instruction.name}")
        print(instruction.generate_code())