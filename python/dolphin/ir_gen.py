from pathlib import Path 
from typing import Dict, List, Optional, Union, Any
import json
import subprocess
import shutil
from dataclasses import asdict

from .parser import SolanaParser
from .core.types import (
    SolanaType, AccountDefinition, InstructionDefinition,
    AccountField, InstructionAccount
)
from .ir import (
    IRProgram, IRAccount, IRInstruction, IRField,
    IRArgument, IRAccountUsage, IRStatement, IRRequire,
    IRExpression, IRLiteral, IRVariable, IRBinaryOp,
    IRRequireData, SpanData, IRMethodCall, IRList,
    to_json
)
from .templates import read_template, TEMPLATES

class IRGenerator:
    """IR Generator that creates intermediate representation for Dolphin programs"""
    
    def __init__(self, source_code: str):
        self.parser = SolanaParser(source_code)
        self.program: Optional[IRProgram] = None
        
    def generate(self) -> IRProgram:
        """Generate IR from source code"""
        self.program = self.parser.parse()
        self._process_program()
        return self.program
        
    def _process_program(self):
        """Process program-level IR nodes"""
        if not self.program:
            raise ValueError("No program parsed")
            
        # Extract program_id from IRLiteral if needed
        if isinstance(self.program.program_id, IRLiteral):
            self.program.program_id = self.program.program_id.data["value"]
            
        # Process accounts
        for account in self.program.accounts:
            self._process_account(account)
            
        # Process instructions
        for instruction in self.program.instructions:
            self._process_instruction(instruction)
    
    def _process_account(self, account: IRAccount):
        """Process account-level IR nodes"""
        # Convert to AccountDefinition for validation
        account_def = AccountDefinition(
            name=account.name,
            fields=[
                AccountField(
                    name=field.name,
                    type_name=field.type_name,
                    attributes=field.attributes
                )
                for field in account.fields
            ],
            is_pda=account.is_pda,
            seeds=account.seeds,
            discriminator=account.discriminator
        )
        
        # Ensure seeds are properly formatted
        if account.seeds:
            processed_seeds = []
            for seed in account.seeds:
                if isinstance(seed, str):
                    if seed.startswith('"') and seed.endswith('"'):
                        # String literal seed
                        processed_seeds.append(seed)
                    else:
                        # Variable reference seed
                        processed_seeds.append(seed)
                else:
                    # Handle other types of seeds
                    processed_seeds.append(str(seed))
            account.seeds = processed_seeds
        
        # Handle PDA configuration
        if account.is_pda:
            # Add default discriminator
            if not account_def.discriminator:
                account_def.discriminator = f"{account_def.name.lower()}_type"
                account.discriminator = account_def.discriminator
            
            # Process PDA seeds
            if account.seeds:
                # Debug output
                print(f"\nProcessed PDA seeds for {account.name}:")
                for seed in account.seeds:
                    if isinstance(seed, IRLiteral):
                        print(f"  String literal: {seed.data['value']}")
                    elif isinstance(seed, IRVariable):
                        print(f"  Variable reference: {seed.data['name']}")
            
        # Validate and normalize field types
        for field, ir_field in zip(account_def.fields, account.fields):
            normalized_type = self._validate_and_normalize_type(field.type_name)
            field.type_name = normalized_type
            ir_field.type_name = normalized_type
            
    def _process_instruction(self, instruction: IRInstruction):
        """Process instruction-level IR nodes"""
        # Convert to InstructionDefinition for validation
        instruction_def = InstructionDefinition(
            name=instruction.name,
            arguments=[
                IRArgument(name=arg.name, type_name=arg.type_name)
                for arg in instruction.args
            ],
            accounts=[
                InstructionAccount(
                    name=acc.name,
                    account_type=acc.account_type,
                    is_mutable=acc.is_mutable,
                    is_signer=acc.is_signer
                )
                for acc in instruction.accounts
            ],
            body=[]  # Body will be processed separately
        )
        
        # Add necessary validation statements
        self._add_account_validations(instruction, instruction_def)
        
        # Process instruction body
        processed_body = []
        for stmt in instruction.body:
            processed_stmt = self._process_statement(stmt)
            if processed_stmt:
                processed_body.append(processed_stmt)
        instruction.body = processed_body
        
    def _process_statement(self, stmt: IRStatement) -> Optional[IRStatement]:
        """Process individual statements"""
        if stmt.kind == "Require":
            return self._process_require(stmt)
        elif stmt.kind == "Assignment":
            return self._process_assignment(stmt)
        elif stmt.kind == "MethodCall":
            return self._process_method_call(stmt)
        elif stmt.kind == "Assert":
            assert_data = stmt.data
            test = assert_data.get("test", {})
            
            # Check if this is a signer validation
            if isinstance(test, dict) and "kind" in test:
                kind_data = test["kind"]
                if isinstance(kind_data, dict) and "BinaryOp" in kind_data:
                    binary_op = kind_data["BinaryOp"]
                    if binary_op.get("op") == "==":
                        left = binary_op.get("left", {}).get("kind", {}).get("Variable", "")
                        right = binary_op.get("right", {}).get("kind", {}).get("Variable", "")
                        
                        # Check if this is a signer comparison
                        if "signer" in str(right):
                            parts = [p for p in left.split('.') if p not in {"self"}]
                            if len(parts) >= 2 and parts[-1] == "authority":
                                account_name = parts[0]
                                return IRRequire(
                                    IRRequireData(
                                        condition=test,
                                        message=f"{account_name} must be signer",
                                        span=SpanData(0, 0)
                                    )
                                )
            
            # For non-signer asserts, preserve the test condition
            return IRRequire(
                IRRequireData(
                    condition=test,
                    message="assertion failed",
                    span=SpanData(0, 0)
                )
            )
        return stmt

    def _process_assignment(self, stmt: IRStatement) -> IRStatement:
        """Process assignment statements"""
        return IRStatement(
            kind="Assignment",
            data={
                "target": stmt.data.get("target", ""),
                "operator": stmt.data.get("operator", "="),  # Preserve the operator
                "value": self._process_expression(stmt.data.get("value", {}))
            }
        )
        
    def _process_require(self, stmt: IRStatement) -> IRStatement:
        """Process require statements and enhance signer validation messages"""
        require_data = stmt.data.get("data", {})
        # Extract span data safely
        span_data = require_data.get("span", {})
        if isinstance(span_data, SpanData):
            span = span_data
        elif isinstance(span_data, dict):
            span = SpanData(
                line=span_data.get("line", 0),
                column=span_data.get("column", 0)
            )
        else:
            span = SpanData(0, 0)

        condition = self._process_expression(require_data.get("condition", {}))
        original_message = require_data.get("message", "assertion failed")
        new_message = original_message

        # Check for signer validation pattern
        if isinstance(condition, IRBinaryOp) and condition.data["op"] == "==":
            left = condition.data["left"]
            right = condition.data["right"]
            
            # Check both sides of the equality comparison
            for (l, r) in [(left, right), (right, left)]:
                if (isinstance(l, IRVariable) and 
                    isinstance(r, IRVariable) and 
                    r.data.get("name") == "signer"):
                    # Extract account name from variable path (e.g. "counter.authority" -> "counter")
                    parts = l.data["name"].split('.')
                    if len(parts) >= 2 and parts[-1] == "authority":
                        account_name = parts[-2]  # Get second to last part
                        new_message = f"{account_name} must be signer"
                        break

        processed_data = IRRequireData(
            condition=condition,
            message=new_message,
            span=span
        )
        return IRRequire(processed_data)
            
    def _process_method_call(self, stmt: IRStatement) -> IRStatement:
        """Process method call statements"""
        call_data = stmt.data
        processed_args = [
            self._process_expression(arg) for arg in call_data["args"]
        ]
        return IRMethodCall(
            target=call_data["target"],
            method=call_data["method"],
            args=processed_args
        )
        
    def _process_expression(self, expr: Union[IRExpression, Dict]) -> Union[IRExpression, Dict]:
        """Process expressions"""
        if isinstance(expr, dict):
            # If this is already a properly formatted dict with kind and Literal, return it as is
            if "kind" in expr and "Literal" in expr["kind"]:
                return expr
                
            # Handle nested kind structure which is the standard format
            kind_data = expr.get("kind", {})
            if isinstance(kind_data, dict):
                # Handle Rust's Literal enum variants
                if any(variant in kind_data for variant in ("Integer", "Float", "String", "Boolean")):
                    variant, value = next(iter(kind_data.items()))
                    # Return in the expected dict format
                    return {
                        "kind": {
                            "Literal": {
                                "value": value
                            }
                        },
                        "span": {
                            "start": 0,
                            "end": 0,
                            "line": 0,
                            "column": 0
                        }
                    }
                elif "Variable" in kind_data:
                    return IRVariable(kind_data["Variable"])
                elif "List" in kind_data:
                    list_data = kind_data["List"]
                    return IRList([
                        self._process_expression(element) 
                        for element in list_data
                    ])
                elif "BinaryOp" in kind_data:
                    binary_data = kind_data["BinaryOp"]
                    # Create proper span information
                    span = SpanData(0, 0)  # Default span
                    if "span" in expr:
                        span = SpanData(
                            line=expr["span"].get("line", 0),
                            column=expr["span"].get("column", 0)
                        )
                    
                    # Process left and right expressions
                    left = self._process_expression(binary_data.get("left", {}))
                    right = self._process_expression(binary_data.get("right", {}))
                    
                    # Special handling for signer comparisons
                    if (isinstance(right, IRVariable) and 
                        "signer" in right.data.get("name", "") and 
                        isinstance(left, IRVariable)):
                        # Extract account name from left side
                        parts = [p for p in left.data["name"].split('.') if p not in {"self"}]
                        if len(parts) >= 2 and parts[-1] == "authority":
                            account_name = parts[0]
                            return IRBinaryOp(
                                "==",
                                IRVariable(f"{account_name}.authority.key()"),
                                IRVariable("signer.key()"),
                                span=span
                            )
                    
                    # Default binary operation
                    return IRBinaryOp(
                        op=binary_data.get("op", "=="),
                        left=left,
                        right=right,
                        span=span
                    )
        elif isinstance(expr, IRExpression):
            return expr
            
        # If we get here, return a properly formatted dict for None
        return {
            "kind": {
                "Literal": {
                    "value": None
                }
            },
            "span": {
                "start": 0,
                "end": 0,
                "line": 0,
                "column": 0
            }
        }
        
    def _add_account_validations(self, instruction: IRInstruction, instruction_def: InstructionDefinition):
        """Add necessary account validation statements"""
        validations = []
        validated_accounts = set()

        # First check for accounts with authority fields
        if self.program and self.program.accounts:
            for account in self.program.accounts:
                account_name = account.name.lower()
                has_authority = any(field.name == "authority" for field in account.fields)
                is_used = any(
                    (stmt.kind == "Assignment" and account_name in stmt.data.get("target", "")) or
                    (stmt.kind == "Assert" and account_name in str(stmt.data.get("test", "")))
                    for stmt in instruction.body
                )
                
                if has_authority and is_used and account_name not in validated_accounts:
                    validations.append(
                        IRRequire(
                            IRRequireData(
                                condition=IRBinaryOp(
                                    "==",
                                    IRVariable(f"{account_name}.authority.key()"),
                                    IRVariable("signer.key()")
                                ),
                                message=f"{account_name} must be signer",
                                span=SpanData(0, 0)
                            )
                        )
                    )
                    validated_accounts.add(account_name)

        # Process existing require statements
        for stmt in instruction.body:
            if stmt.kind == "Require":
                require_data = stmt.data.get("data", {})
                condition = require_data.get("condition", {})
                
                # Check for authority validation pattern
                if isinstance(condition, IRBinaryOp) and condition.op == "==":
                    left = condition.left
                    right = condition.right
                    
                    # Check both sides for signer.key() pattern
                    left_signer = isinstance(left, IRVariable) and "signer.key()" in left.data.get("name", "")
                    right_signer = isinstance(right, IRVariable) and "signer.key()" in right.data.get("name", "")
                    
                    if left_signer or right_signer:
                        # Extract account name from the non-signer side
                        account_side = right if left_signer else left
                        if isinstance(account_side, IRVariable):
                            parts = account_side.data.get("name", "").split(".")
                            if len(parts) >= 3 and parts[1] == "authority" and parts[2] == "key()":
                                account_name = parts[0]
                                if account_name and account_name not in validated_accounts:
                                    validations.append(stmt)
                                    validated_accounts.add(account_name)
        
        # Add signer validations for explicitly marked signer accounts
        for account in instruction_def.accounts:
            if account.is_signer and account.name not in validated_accounts:
                validations.append(
                    IRRequire(
                        IRRequireData(
                            condition=IRBinaryOp(
                                "==",
                                IRVariable(f"{account.name}.key()"),
                                IRVariable("signer.key()")
                            ),
                            message=f"{account.name} must be signer",
                            span=SpanData(0, 0)
                        )
                    )
                )
                validated_accounts.add(account.name)
        
        # Add validations at the beginning of instruction body
        instruction.body = validations + [stmt for stmt in instruction.body if stmt not in validations]
        
    def _validate_and_normalize_type(self, type_name: str) -> str:
        """Validate and normalize field types using SolanaType"""
        try:
            # Try to convert Python type to Solana type
            return SolanaType.from_python_type(type_name)
        except ValueError as e:
            # If not a basic type, check if it's a custom type
            if type_name.startswith("Vec<") or type_name.startswith("Option<"):
                return type_name  # Already in Solana format
            raise ValueError(f"Invalid type: {type_name}") from e

class DolphinGenerator:
    """Main generator class for Dolphin framework"""
    
    def __init__(self, program_path: str):
        self.program_path = Path(program_path)
        self.ir_generator: Optional[IRGenerator] = None
        
    def build_project(self):
        """Build the Dolphin project"""
        program_file = self.program_path / "program" / "lib.py"
        with open(program_file, "r") as f:
            source = f.read()
            
        # Generate IR
        self.ir_generator = IRGenerator(source)
        program_ir = self.ir_generator.generate()
        
        # Convert to JSON
        ir_json = to_json(program_ir)
        
        # Save IR
        ir_path = self.program_path / "target" / "ir.json"
        with open(ir_path, "w") as f:
            json.dump(ir_json, f, indent=2)
            
        print("✨ Successfully generated IR")
        return program_ir
