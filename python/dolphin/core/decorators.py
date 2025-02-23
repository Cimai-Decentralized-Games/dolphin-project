from functools import wraps
from typing import Type, TypeVar, Callable, Any, List, Dict, Optional
from .types import (
    SolanaAccount, 
    AccountDefinition, 
    InstructionDefinition,
    AccountField
)
from ..utils.validation import (
    validate_address,
    validate_program_id,
    validate_identifier,
    validate_type_name,
    validate_account_name,
    validate_field_name,
    validate_instruction_name,
    validate_solana_type,
    ValidationError
)

T = TypeVar('T')

def validate(validation_type: str) -> Callable:
    """
    Decorator for validating Solana-related values.
    
    Args:
        validation_type: Type of validation to perform
            ('address', 'program_id', 'identifier', 'type_name',
             'account_name', 'field_name', 'instruction_name', 'solana_type')
    """
    validation_funcs = {
        'address': validate_address,
        'program_id': validate_program_id,
        'identifier': validate_identifier,
        'type_name': validate_type_name,
        'account_name': validate_account_name,
        'field_name': validate_field_name,
        'instruction_name': validate_instruction_name,
        'solana_type': validate_solana_type
    }
    
    if validation_type not in validation_funcs:
        raise ValueError(f"Unknown validation type: {validation_type}")
        
    validate_func = validation_funcs[validation_type]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the value to validate from first argument after self
            if len(args) > 1:
                value = args[1]
            else:
                # Try to get from kwargs
                param_name = list(kwargs.keys())[0]
                value = kwargs[param_name]
                
            if not validate_func(str(value)):
                raise ValidationError(f"Invalid {validation_type}: {value}")
                
            return func(*args, **kwargs)
        return wrapper
    return decorator


def program(program_id: str, name: Optional[str] = None, version: str = "0.1.0"):
    """
    Decorator for Solana program classes.
    
    Args:
        program_id: The program's public key on Solana
        name: Optional program name (defaults to class name)
        version: Program version string
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Set program metadata
        cls.PROGRAM_ID = program_id
        cls.PROGRAM_NAME = name or cls.__name__
        cls.PROGRAM_VERSION = version
        
        # Store original init
        original_init = cls.__init__
        
        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.program_id = program_id
            self.accounts: List[AccountDefinition] = []
            self.instructions: List[InstructionDefinition] = []
            
        cls.__init__ = new_init
        return cls
    
    return decorator

def account(seeds: Optional[List[str]] = None, discriminator: Optional[str] = None):
    """
    Decorator for Solana account structures.
    
    Args:
        seeds: Optional list of PDA seeds
        discriminator: Optional account discriminator
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Create AccountDefinition
        account_def = AccountDefinition(
            name=cls.__name__,
            fields=[],
            is_pda=bool(seeds),
            seeds=seeds or [],
            discriminator=discriminator
        )
        
        # Process class annotations for fields
        for name, type_hint in cls.__annotations__.items():
            if not name.startswith('_'):
                field = AccountField(
                    name=name,
                    type_name=type_hint.__name__ if hasattr(type_hint, '__name__') else str(type_hint),
                    attributes=[]
                )
                account_def.add_field(field.name, field.type_name)
        
        # Store account definition
        cls._account_definition = account_def
        
        # Store original init
        original_init = cls.__init__
        
        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self._is_account = True
            self._seeds = seeds
            self._discriminator = discriminator
            
        cls.__init__ = new_init
        return cls
    
    return decorator

def instruction(
    name: Optional[str] = None, 
    accounts: Optional[Dict[str, Dict[str, bool]]] = None
):
    """
    Decorator for program instruction methods.
    
    Args:
        name: Optional instruction name (defaults to method name)
        accounts: Dictionary of required accounts with their properties
                 e.g., {"token_account": {"mutable": True, "signer": False}}
    """
    def decorator(func: Callable) -> Callable:
        instruction_name = name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create instruction definition if not exists
            if not hasattr(func, '_instruction_definition'):
                func._instruction_definition = InstructionDefinition(
                    name=instruction_name,
                    arguments=[],
                    accounts=[],
                    body=[]
                )
                
                # Add accounts if specified
                if accounts:
                    for acc_name, properties in accounts.items():
                        func._instruction_definition.add_account(
                            name=acc_name,
                            account_type="Account",  # This will be updated during IR generation
                            is_mutable=properties.get("mutable", False),
                            is_signer=properties.get("signer", False)
                        )
            
            return func(*args, **kwargs)
        
        # Store metadata
        wrapper._instruction_name = instruction_name
        wrapper._accounts = accounts or {}
        
        return wrapper
    return decorator

def pda(*seed_fields: str):
    """
    Decorator to mark an account as a PDA and specify its seeds.
    
    Args:
        *seed_fields: Names of the fields to use as seeds
    """
    def decorator(cls: Type[T]) -> Type[T]:
        if hasattr(cls, '_account_definition'):
            cls._account_definition.set_pda(list(seed_fields))
        return cls
    return decorator

def mutable(func: Callable) -> Callable:
    """Decorator to mark an account field as mutable."""
    if hasattr(func, '_field_attributes'):
        func._field_attributes.append('mutable')
    else:
        func._field_attributes = ['mutable']
    return func

def signer(func: Callable) -> Callable:
    """Decorator to mark an account as a required signer."""
    if hasattr(func, '_field_attributes'):
        func._field_attributes.append('signer')
    else:
        func._field_attributes = ['signer']
    return func
