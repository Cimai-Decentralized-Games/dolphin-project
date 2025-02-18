"""Dolphin: Python-to-Solana Framework"""
# Import Rust-generated module first
try:
    from dolphin import (
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

# Import Python modules
from dolphin.parser import SolanaParser
from dolphin.dl.parser import DLParser
from dolphin.core.types import *
from dolphin.core.decorators import program, account, instruction, pda
from dolphin.ir_gen import IRGenerator, generate_ir
from dolphin.utils import utils

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
    # Parsers
    'SolanaParser',
    'DLParser',
    # Utils
    'utils',
    # Version info
    '__version__',
    'version',
]