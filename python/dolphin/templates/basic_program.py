"""
Basic Dolphin Program Template
This template provides a simple counter program structure.
"""

from dolphin.prelude import *

@program("PROGRAM_ID_PLACEHOLDER")
class BasicProgram:
    """A basic Solana program demonstrating account management and instructions"""
    
    @account
    class Counter:
        """Counter account storing the state"""
        authority: Pubkey
        count: u64
        
    @instruction
    def initialize(
        self,
        counter: Counter,
        authority: Signer,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        """Initialize the counter account
        
        Args:
            counter: The counter account to initialize
            authority: The account that can modify the counter
            system_program: The system program
        """
        counter.authority = authority.key()
        counter.count = 0
        
    @instruction
    def increment(
        self,
        counter: Counter,
        authority: Signer
    ):
        """Increment the counter
        
        Args:
            counter: The counter account to increment
            authority: Must match the account's authority
        """
        assert counter.authority == authority.key(), "Invalid authority"
        counter.count += 1
        
    @instruction
    def decrement(
        self,
        counter: Counter,
        authority: Signer
    ):
        """Decrement the counter
        
        Args:
            counter: The counter account to decrement
            authority: Must match the account's authority
        """
        assert counter.authority == authority.key(), "Invalid authority"
        assert counter.count > 0, "Counter already at 0"
        counter.count -= 1
