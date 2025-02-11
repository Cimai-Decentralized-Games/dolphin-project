from functools import wraps
from typing import Type, TypeVar, Callable, Any
from .types import SolanaAccount

T = TypeVar('T')

def program(program_id: str):
    """
    Decorator for Solana program classes.
    
    Args:
        program_id: The program's public key on Solana
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Set program metadata
        cls.PROGRAM_ID = program_id
        
        # Store original init
        original_init = cls.__init__
        
        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            # Initialize program with original init
            original_init(self, *args, **kwargs)
            # Set program ID as instance attribute
            self.program_id = program_id
            
        cls.__init__ = new_init
        return cls
    
    return decorator

def account(account_type: Type[SolanaAccount]):
    """
    Decorator for account instruction handlers.
    
    Args:
        account_type: The type of Solana account this handler processes
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Validate account type
            if not isinstance(args[1], account_type):
                raise TypeError(f"Expected account type {account_type.__name__}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def instruction(instruction_name: str):
    """
    Decorator for program instruction methods.
    
    Args:
        instruction_name: Name of the instruction
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Add instruction context
            setattr(func, '_instruction_name', instruction_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator
