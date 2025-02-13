from typing import Dict, Set, Optional, List
from dataclasses import dataclass
from .ast import *
from .utils.validation import validate_program_id, validate_identifier

@dataclass
class SymbolInfo:
    """Information about a symbol in the symbol table"""
    type_name: str
    is_mutable: bool = True
    is_initialized: bool = False
    scope: str = "global"
    node: Optional[Node] = None

class SolanaAnalyzer:
    def __init__(self):
        self.symbol_table: Dict[str, SymbolInfo] = {}
        self.current_scope: str = "global"
        self.current_account: Optional[str] = None
        self.current_instruction: Optional[str] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def analyze(self, program: Program) -> bool:
        """Analyze the entire program"""
        # Validate program structure
        if not validate_program_id(program.program_id):
            self.errors.append(f"Invalid program ID: {program.program_id}")
        
        if not validate_identifier(program.name):
            self.errors.append(f"Invalid program name: {program.name}")

        # Analyze accounts
        for account in program.accounts:
            self.analyze_account(account)

        # Analyze instructions
        for instruction in program.instructions:
            self.analyze_instruction(instruction)

        # Analyze remaining statements
        for stmt in program.statements:
            self.analyze_statement(stmt)

        return len(self.errors) == 0

    def analyze_account(self, account: AccountDef) -> None:
        """Analyze account definition"""
        self.current_scope = f"account:{account.name}"
        self.current_account = account.name

        # Check account name
        if not validate_identifier(account.name):
            self.errors.append(f"Invalid account name: {account.name}")

        # Check for duplicate account definitions
        if account.name in self.symbol_table:
            self.errors.append(f"Duplicate account definition: {account.name}")
            return

        # Analyze PDA configuration
        if account.is_pda:
            self.analyze_pda_seeds(account)

        # Analyze fields
        seen_fields: Set[str] = set()
        for field in account.fields:
            if field.name in seen_fields:
                self.errors.append(f"Duplicate field '{field.name}' in account {account.name}")
                continue
            seen_fields.add(field.name)
            self.analyze_field(field, account.name)

        self.symbol_table[account.name] = SymbolInfo(
            type_name="Account",
            is_mutable=False,
            scope=self.current_scope,
            node=account
        )

        self.current_account = None
        self.current_scope = "global"

    def analyze_instruction(self, instruction: InstructionDef) -> None:
        """Analyze instruction definition"""
        self.current_scope = f"instruction:{instruction.name}"
        self.current_instruction = instruction.name

        # Check instruction name
        if not validate_identifier(instruction.name):
            self.errors.append(f"Invalid instruction name: {instruction.name}")

        # Check for duplicate instruction definitions
        if instruction.name in self.symbol_table:
            self.errors.append(f"Duplicate instruction definition: {instruction.name}")
            return

        # Analyze arguments
        seen_args: Set[str] = set()
        for arg in instruction.args:
            if arg.name in seen_args:
                self.errors.append(
                    f"Duplicate argument '{arg.name}' in instruction {instruction.name}"
                )
                continue
            seen_args.add(arg.name)
            self.analyze_argument(arg)

        # Analyze account usage
        seen_accounts: Set[str] = set()
        for account in instruction.accounts:
            if account.name in seen_accounts:
                self.errors.append(
                    f"Duplicate account usage '{account.name}' in instruction {instruction.name}"
                )
                continue
            seen_accounts.add(account.name)
            self.analyze_account_usage(account)

        # Create new scope for instruction body
        for stmt in instruction.body:
            self.analyze_statement(stmt)

        self.current_instruction = None
        self.current_scope = "global"

    def analyze_field(self, field: FieldDef, account_name: str) -> None:
        """Analyze account field definition"""
        if not validate_identifier(field.name):
            self.errors.append(f"Invalid field name: {field.name}")

        # Check field type
        if not self.is_valid_solana_type(field.type_name):
            self.errors.append(
                f"Invalid type '{field.type_name}' for field '{field.name}' in account {account_name}"
            )

        # Add to symbol table
        self.symbol_table[f"{account_name}.{field.name}"] = SymbolInfo(
            type_name=field.type_name,
            is_mutable=True,
            scope=self.current_scope,
            node=field
        )

    def analyze_statement(self, stmt: Statement) -> None:
        """Analyze a statement"""
        if isinstance(stmt, Assignment):
            self.analyze_assignment(stmt)
        elif isinstance(stmt, MethodCall):
            self.analyze_method_call(stmt)
        elif isinstance(stmt, VariableDeclaration):
            self.analyze_variable_declaration(stmt)

    def analyze_expression(self, expr: Expression) -> Optional[str]:
        """Analyze an expression and return its type"""
        if isinstance(expr, Literal):
            return expr.type_name
        elif isinstance(expr, VariableReference):
            return self.get_variable_type(expr.name)
        elif isinstance(expr, BinaryOp):
            return self.analyze_binary_op(expr)
        elif isinstance(expr, Call):
            return self.analyze_call(expr)
        elif isinstance(expr, AttributeAccess):
            return self.analyze_attribute_access(expr)
        return None

    def is_valid_solana_type(self, type_name: str) -> bool:
        """Check if a type is valid for Solana"""
        basic_types = {
            "u8", "u16", "u32", "u64",
            "i8", "i16", "i32", "i64",
            "bool", "String", "Pubkey"
        }
        
        if type_name in basic_types:
            return True
            
        # Check Vec<T>
        if type_name.startswith("Vec<") and type_name.endswith(">"):
            inner_type = type_name[4:-1]
            return self.is_valid_solana_type(inner_type)
            
        # Check Option<T>
        if type_name.startswith("Option<") and type_name.endswith(">"):
            inner_type = type_name[7:-1]
            return self.is_valid_solana_type(inner_type)
            
        # Check if it's a defined account type
        return type_name in self.symbol_table and self.symbol_table[type_name].type_name == "Account"

    def get_error_context(self, node: Node) -> str:
        """Get error context information"""
        context = f"line {node.line}, column {node.column}"
        if self.current_account:
            context += f" in account {self.current_account}"
        if self.current_instruction:
            context += f" in instruction {self.current_instruction}"
        return context

    def analyze_pda_seeds(self, account: AccountDef) -> None:
        """Analyze PDA seeds configuration"""
        for seed in account.seeds:
            if not isinstance(seed, str):
                self.errors.append(f"Invalid PDA seed in account {account.name}")
            elif not any(f.name == seed for f in account.fields):
                self.warnings.append(
                    f"PDA seed '{seed}' not found in account {account.name} fields"
                )
