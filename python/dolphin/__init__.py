# Import Rust module
from .dolphin import *  # This imports the Rust-generated module

# Import Python modules
from .parser import SolanaParser
from .ir_gen import IRGenerator

# You might want to control what's exposed in __all__ if needed
__all__ = ['SolanaParser', 'IRGenerator']