import ast
from typing import Dict, Set, Optional, List
from dataclasses import dataclass
from .ir import IRProgram, IRAccount, IRInstruction, IRField  # Import IR classes
from .utils.validation import validate_program_id, validate_identifier


@dataclass
class SymbolInfo:
    """Information about a symbol in the symbol table"""
    type_name: str
    is_mutable: bool = True
    is_initialized: bool = False
    scope: str = "global"
    node: Optional[ast.AST] = None  # Use ast.AST instead of Node


class SolanaAnalyzer:
    def __init__(self):
        self.symbol_table: Dict[str, SymbolInfo] = {}
        self.current_scope: str = "global"
        self.current_account: Optional[str] = None
        self.current_instruction: Optional[str] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def analyze(self, ir_program: IRProgram) -> bool:
        """Analyze the entire program (now takes IRProgram)"""
        # Validate program structure
        if not validate_program_id(ir_program.program_id):
            self.errors.append(f"Invalid program ID: {ir_program.program_id}")

        if not validate_identifier(ir_program.name):
            self.errors.append(f"Invalid program name: {ir_program.name}")

        # Analyze accounts
        for account in ir_program.accounts:
            self.analyze_account(account)

        # Analyze instructions
        for instruction in ir_program.instructions:
            self.analyze_instruction(instruction)

        return len(self.errors) == 0

    def analyze_account(self, account: IRAccount) -> None:
        """Analyze account definition (now takes IRAccount)"""
        self.current_scope = f"account:{account.name}"
        self.current_account = account.name

        # Check account name
        if not validate_identifier(account.name):
            self.errors.append(f"Invalid account name: {account.name}")

        # Check for duplicate account definitions
        if account.name in self.symbol_table:
            self.errors.append(f"Duplicate account definition: {account.name}")
            return

        # Analyze fields
        seen_fields: Set[str] = set()
        for field in account.fields:
            if field.name in seen_fields:
                self.errors.append(f"Duplicate field '{field.name}' in account {account.name}")
                continue
            seen_fields.add(field.name)
            self.analyze_field(account.name, field)  # Pass IRField as node

        self.symbol_table[account.name] = SymbolInfo(
            type_name="Account",
            is_mutable=False,
            scope=self.current_scope,
            node=None  # No AST node here, using IR
        )

        self.current_account = None
        self.current_scope = "global"

    def analyze_instruction(self, instruction: IRInstruction) -> None:
        """Analyze instruction definition (now takes IRInstruction)"""
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
            #self.analyze_argument(arg)  #No analyze_argument anymore

        # Analyze account usage
        seen_accounts: Set[str] = set()
        for account in instruction.accounts:
            if account.name in seen_accounts:
                self.errors.append(
                    f"Duplicate account usage '{account.name}' in instruction {instruction.name}"
                )
                continue
            seen_accounts.add(account.name)
            #self.analyze_account_usage(account) #No analyze_account_usage anymore

        # Create new scope for instruction body
        #Analyze the IR Statements.  There is no more need for AST here.  The AST information has already been extracted
        for stmt in instruction.body:
            self.analyze_statement(stmt)

        self.current_instruction = None
        self.current_scope = "global"

    def analyze_field(self, account_name: str, field: IRField) -> None:
        """Analyze account field definition. Uses IRField now"""
        if not validate_identifier(field.name):  # Pass field.name, not field
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
            node=None  # No AST node here, using IR
        )

    def analyze_statement(self, stmt) -> None:
        """Analyze a statement (Now, IRStatement). No AST analysis"""
        #This will have to be filled in as you implement statements inside of IRStatement.
        #This does not analyze any AST node.  The AST has already been parsed in the parser and created into IR.

        #if isinstance(stmt, Assignment):
        #    self.analyze_assignment(stmt)
        #elif isinstance(stmt, MethodCall):
        #    self.analyze_method_call(stmt)
        #elif isinstance(stmt, VariableDeclaration):
        #    self.analyze_variable_declaration(stmt)
        pass

    def analyze_expression(self, expr) -> Optional[str]:
        """Analyze an expression and return its type (Now, IRExpression)"""
        #if isinstance(expr, Literal):
        #    return expr.type_name
        #elif isinstance(expr, VariableReference):
        #    return self.get_variable_type(expr.name)
        #elif isinstance(expr, BinaryOp):
        #    return self.analyze_binary_op(expr)
        #elif isinstance(expr, Call):
        #    return self.analyze_call(expr)
        #elif isinstance(expr, AttributeAccess):
        #    return self.analyze_attribute_access(expr)
        #return None
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

    def get_error_context(self, node: Optional[ast.AST]) -> str:
        """Get error context information. Now only uses the AST if available"""
        if node and hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
            context = f"line {node.lineno}, column {node.col_offset}"
        else:
            context = "Unknown location" #Fallback if no AST node

        if self.current_account:
            context += f" in account {self.current_account}"
        if self.current_instruction:
            context += f" in instruction {self.current_instruction}"
        return context

    def analyze_pda_seeds(self, account: IRAccount) -> None:
        """Analyze PDA seeds configuration (Now uses IRAccount)"""
        for seed in account.seeds:
            if not isinstance(seed, str):
                self.errors.append(f"Invalid PDA seed in account {account.name}")
            elif not any(f.name == seed for f in account.fields):
                self.warnings.append(
                    f"PDA seed '{seed}' not found in account {account.name} fields"
                )