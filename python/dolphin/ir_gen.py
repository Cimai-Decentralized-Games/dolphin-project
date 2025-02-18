from pathlib import Path 
from typing import Dict, List, Optional, Union, Any
import json
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
    IRRequireData, SpanData, IRMethodCall,
    to_json
)

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
        
        # Add default discriminator if PDA
        if account_def.is_pda and not account_def.discriminator:
            account_def.discriminator = f"{account_def.name.lower()}_type"
            account.discriminator = account_def.discriminator
            
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
        if stmt.kind == "require":
            return self._process_require(stmt)
        elif stmt.kind == "assignment":
            return self._process_assignment(stmt)
        elif stmt.kind == "method_call":
            return self._process_method_call(stmt)
        return stmt

    def _process_assignment(self, stmt: IRStatement) -> IRStatement:
        """Process assignment statements"""
        return IRStatement(
            kind="assignment",
            data={
                "target": stmt.data["target"],
                "value": self._process_expression(stmt.data["value"])
            }
        )
        
    def _process_require(self, stmt: IRStatement) -> IRStatement:
        """Process require statements"""
        require_data = stmt.data
        processed_data = IRRequireData(
            condition=self._process_expression(require_data["condition"]),
            message=require_data["message"],
            span=SpanData(
                line=require_data.get("span", {}).get("line", 0),
                column=require_data.get("span", {}).get("column", 0)
            )
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
            if expr.get("kind") == "literal":
                return IRLiteral(expr["data"]["value"])
            elif expr.get("kind") == "variable":
                return IRVariable(expr["data"]["name"])
            elif expr.get("kind") == "binary_op":
                return IRBinaryOp(
                    expr["data"]["op"],
                    self._process_expression(expr["data"]["left"]),
                    self._process_expression(expr["data"]["right"])
                )
        return expr
        
    def _add_account_validations(self, instruction: IRInstruction, instruction_def: InstructionDefinition):
        """Add necessary account validation statements"""
        validations = []
        
        # Process existing assert/require statements to identify signer checks
        for stmt in instruction.body:
            if stmt.kind == "require":
                if isinstance(stmt.data.get("condition", {}), dict):
                    condition = stmt.data["condition"]
                    if (condition.get("kind") == "binary_op" and
                        condition["data"].get("op") == "==" and
                        "authority" in str(condition["data"].get("left", {})) and
                        "signer" in str(condition["data"].get("right", {}))):
                        # This is a signer validation check - preserve the original message
                        validations.append(stmt)
        
        # Add any additional signer validations from account definitions
        for account in instruction_def.accounts:
            if account.is_signer and not any("signer" in str(v.data.get("message")) for v in validations):
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
