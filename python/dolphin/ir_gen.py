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
        return stmt

    def _process_assignment(self, stmt: IRStatement) -> IRStatement:
        """Process assignment statements"""
        return IRStatement(
            kind="Assignment",
            data={
                "target": stmt.data.get("target", ""),
                "value": self._process_expression(stmt.data.get("value", {}))
            }
        )
        
    def _process_require(self, stmt: IRStatement) -> IRStatement:
        """Process require statements"""
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

        processed_data = IRRequireData(
            condition=self._process_expression(require_data.get("condition", {})),
            message=require_data.get("message", "assertion failed"),
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
        
    def _process_expression(self, expr: Union[IRExpression, Dict]) -> IRExpression:
        """Process expressions"""
        if isinstance(expr, dict):
            # Handle nested kind structure which is the standard format
            kind_data = expr.get("kind", {})
            if isinstance(kind_data, dict):
                # Handle Rust's Literal enum variants
                if any(variant in kind_data for variant in ("Integer", "Float", "String", "Boolean")):
                    variant, value = next(iter(kind_data.items()))
                    return IRLiteral(value)
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
                    return IRBinaryOp(
                        op=binary_data["op"],
                        left=self._process_expression(binary_data["left"]),
                        right=self._process_expression(binary_data["right"]),
                        span=span
                    )
        elif isinstance(expr, IRExpression):
            return expr
        return IRLiteral(None)  # Default fallback
        
    def _add_account_validations(self, instruction: IRInstruction, instruction_def: InstructionDefinition):
        """Add necessary account validation statements"""
        validations = []
        
        # Process existing assert/require statements to identify signer checks
        for stmt in instruction.body:
            if stmt.kind == "Require":
                require_data = stmt.data["data"]
                condition = (require_data.condition 
                           if isinstance(require_data, IRRequireData)
                           else require_data.get("condition", {}))
                
                # Handle both IRExpression and dict conditions
                if isinstance(condition, IRExpression):
                    is_signer_check = (
                        condition.kind == "BinaryOp" and
                        condition.data["op"] == "==" and
                        "authority" in str(condition.data["left"]) and
                        "signer" in str(condition.data["right"])
                    )
                else:
                    is_signer_check = (
                        condition.get("kind") == "BinaryOp" and
                        condition.get("data", {}).get("op") == "==" and
                        "authority" in str(condition.get("data", {}).get("left", {})) and
                        "signer" in str(condition.get("data", {}).get("right", {}))
                    )
                
                if is_signer_check:
                    validations.append(stmt)
        
        # Add any additional signer validations from account definitions
        for account in instruction_def.accounts:
            if account.is_signer and not any("signer" in str(v.data["data"].message) 
                                           if isinstance(v.data["data"], IRRequireData)
                                           else "signer" in str(v.data.get("data", {}).get("message"))
                                           for v in validations):
                validations.append(
                    IRRequire(
                        IRRequireData(
                            condition=IRBinaryOp(
                                "==",
                                IRVariable(f"{account.name}.key()"),
                                IRVariable("signer.key()")
                            ),
                            message="signer validation required",
                            span=SpanData(0, 0)
                        )
                    )
                )
        
        # Add validations at the beginning of the instruction body
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
