"""Dolphin Language Compiler"""
from ..ir import IR
from .parser import DLParser

def compile_dl(file_path: str) -> IR:
    """Compile a .dl file to IR"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    parser = DLParser(content)
    program = parser.parse()
    return program