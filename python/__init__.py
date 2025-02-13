"""Dolphin: Python-to-Solana Framework"""
from dolphin.core.types import *
from dolphin.core.decorators import program, account, instruction, pda
from dolphin.ir_gen import IRGenerator, generate_ir
from dolphin import utils

try:
    from dolphin.native import (
        AccountGenerator,
        ProgramGenerator,
        InstructionGenerator,
        validation,
        __version__,
        version
    )
except ImportError as e:
    raise ImportError(
        "Failed to import Dolphin native extensions. "
        "Make sure the Rust components are properly built: {}".format(e)
    )

__all__ = [
    # Core decorators
    'program',
    'account',
    'instruction',
    'pda',
    
    # Generators
    'AccountGenerator',
    'ProgramGenerator',
    'InstructionGenerator',
    
    # IR Generation
    'IRGenerator',
    'generate_ir',
    
    # Version info
    '__version__',
    'version',
]