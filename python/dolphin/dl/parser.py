"""Dolphin Language Parser"""
from typing import List, Dict, Optional, Any
import re
from dataclasses import dataclass
from ..ir import (
    IRProgram, IRAccount, IRInstruction, IRField,
    IRStatement, IRExpression, IRLiteral, IRVariable
)

@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

class DLParser:
    def __init__(self, content: str):
        self.content = content
        self.lines = content.splitlines()
        self.current_line = 0
        self.current_pos = 0
        self.tokens: List[Token] = []
        
        # Keywords and symbols
        self.keywords = {
            'program', 'account', 'ix', 'require',
            'if', 'else', 'for', 'while',
            'pubkey', 'string', 'u8', 'u16', 'u32', 'u64',
            'i8', 'i16', 'i32', 'i64', 'bool'
        }
        
    def parse(self) -> IRProgram:
        """Parse .dl file into IR"""
        self._tokenize()
        return self._parse_program()
        
    def _tokenize(self):
        """Convert content into tokens"""
        token_patterns = [
            ('WHITESPACE', r'[ \t]+'),
            ('NEWLINE', r'\n'),
            ('COMMENT', r'//.*'),
            ('STRING', r'"[^"]*"'),
            ('ID', r'[a-zA-Z_][a-zA-Z0-9_]*'),
            ('NUMBER', r'\d+'),
            ('SYMBOL', r'[{}\[\]():,@=+\-*/.<>!]'),
        ]
        
        combined_pattern = '|'.join(f'(?P<{name}>{pattern})' 
                                  for name, pattern in token_patterns)
        token_re = re.compile(combined_pattern)
        
        line = 1
        column = 0
        
        pos = 0
        while pos < len(self.content):
            match = token_re.match(self.content, pos)
            if match is None:
                raise SyntaxError(f"Invalid syntax at line {line}, column {column}")
                
            type_name = match.lastgroup
            value = match.group()
            
            if type_name != 'WHITESPACE' and type_name != 'COMMENT':
                self.tokens.append(Token(type_name, value, line, column))
                
            if type_name == 'NEWLINE':
                line += 1
                column = 0
            else:
                column += len(value)
                
            pos = match.end()
            
    def _parse_program(self) -> IRProgram:
        """Parse program definition"""
        self._expect('ID', 'program')
        name = self._expect('ID').value
        self._expect('SYMBOL', '{')
        
        program_id = None
        accounts = []
        instructions = []
        
        while self._peek().type != 'SYMBOL' or self._peek().value != '}':
            if self._peek().value == 'id':
                self._advance()  # consume 'id'
                self._expect('SYMBOL', ':')
                program_id = self._expect('STRING').value.strip('"')
            elif self._peek().value == 'account':
                accounts.append(self._parse_account())
            elif self._peek().value == 'ix':
                instructions.append(self._parse_instruction())
            else:
                raise SyntaxError(f"Unexpected token at {self._peek().line}:{self._peek().column}")
                
        self._expect('SYMBOL', '}')
        
        return IRProgram(
            name=name,
            program_id=program_id,
            accounts=accounts,
            instructions=instructions
        )
        
    def _parse_account(self) -> IRAccount:
        """Parse account definition"""
        self._expect('ID', 'account')
        name = self._expect('ID').value
        self._expect('SYMBOL', '{')
        
        fields = []
        while self._peek().type != 'SYMBOL' or self._peek().value != '}':
            fields.append(self._parse_field())
            
        self._expect('SYMBOL', '}')
        
        return IRAccount(
            name=name,
            fields=fields
        )
        
    def _parse_field(self) -> IRField:
        """Parse field definition"""
        name = self._expect('ID').value
        self._expect('SYMBOL', ':')
        type_name = self._parse_type()
        
        return IRField(
            name=name,
            type_name=type_name
        )
        
    def _parse_instruction(self) -> IRInstruction:
        """Parse instruction definition"""
        self._expect('ID', 'ix')
        name = self._expect('ID').value
        
        # Parse parameters
        self._expect('SYMBOL', '(')
        args = []
        while self._peek().type != 'SYMBOL' or self._peek().value != ')':
            if args:
                self._expect('SYMBOL', ',')
            arg_name = self._expect('ID').value
            self._expect('SYMBOL', ':')
            arg_type = self._parse_type()
            args.append((arg_name, arg_type))
            
        self._expect('SYMBOL', ')')
        
        # Parse body
        self._expect('SYMBOL', '{')
        statements = []
        while self._peek().type != 'SYMBOL' or self._peek().value != '}':
            statements.append(self._parse_statement())
            
        self._expect('SYMBOL', '}')
        
        return IRInstruction(
            name=name,
            args=args,
            body=statements
        )
        
    def _parse_statement(self) -> IRStatement:
        """Parse a statement"""
        if self._peek().value == 'require':
            return self._parse_require()
        elif self._peek().type == 'ID' and self._peek(1).value == '=':
            return self._parse_assignment()
        else:
            raise SyntaxError(f"Unexpected statement at {self._peek().line}:{self._peek().column}")
            
    def _parse_require(self) -> IRStatement:
        """Parse require statement"""
        self._expect('ID', 'require')
        self._expect('SYMBOL', '(')
        condition = self._parse_expression()
        self._expect('SYMBOL', ',')
        message = self._expect('STRING').value.strip('"')
        self._expect('SYMBOL', ')')
        
        return IRStatement(
            kind="require",
            data={
                "condition": condition,
                "message": message
            }
        )
        
    def _parse_expression(self) -> IRExpression:
        """Parse an expression"""
        if self._peek().type == 'NUMBER':
            return IRLiteral(int(self._advance().value))
        elif self._peek().type == 'STRING':
            return IRLiteral(self._advance().value.strip('"'))
        elif self._peek().type == 'ID':
            return IRVariable(self._advance().value)
        else:
            raise SyntaxError(f"Unexpected expression at {self._peek().line}:{self._peek().column}")
            
    def _expect(self, type_name: str, value: Optional[str] = None) -> Token:
        """Expect a token of given type and optional value"""
        token = self._advance()
        if token.type != type_name:
            raise SyntaxError(
                f"Expected {type_name} but got {token.type} "
                f"at line {token.line}, column {token.column}"
            )
        if value is not None and token.value != value:
            raise SyntaxError(
                f"Expected '{value}' but got '{token.value}' "
                f"at line {token.line}, column {token.column}"
            )
        return token
        
    def _peek(self, ahead: int = 0) -> Token:
        """Look ahead at a token without consuming it"""
        if len(self.tokens) <= ahead:
            raise SyntaxError("Unexpected end of file")
        return self.tokens[ahead]
        
    def _advance(self) -> Token:
        """Consume and return the next token"""
        if not self.tokens:
            raise SyntaxError("Unexpected end of file")
        return self.tokens.pop(0)
        
    def _parse_type(self) -> str:
        """Parse a type name"""
        type_name = self._expect('ID').value
        if type_name not in self.keywords:
            raise SyntaxError(f"Unknown type: {type_name}")
        return type_name