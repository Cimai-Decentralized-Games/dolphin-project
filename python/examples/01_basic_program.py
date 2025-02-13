"""
Basic Solana Program Example
This example shows a simple counter program with increment/decrement instructions
"""
from dolphin.prelude import *

@program("CounterProg111111111111111111111111111111111111")
class CounterProgram:
    @account
    class Counter:
        authority: Pubkey
        count: u64

    @instruction
    def initialize(self, authority: Pubkey):
        """Initialize a new counter account"""
        self.counter.authority = authority
        self.counter.count = 0

    @instruction
    def increment(self):
        """Increment the counter"""
        assert self.counter.authority == self.signer, "Only authority can increment"
        self.counter.count += 1

    @instruction
    def decrement(self):
        """Decrement the counter"""
        assert self.counter.authority == self.signer, "Only authority can decrement"
        assert self.counter.count > 0, "Counter cannot go below zero"
        self.counter.count -= 1