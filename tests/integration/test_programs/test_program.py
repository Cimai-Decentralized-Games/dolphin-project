
from dolphin.prelude import *

@program("Test111111111111111111111111111111111111111")
class TestProgram:
    @account
    class Counter:
        authority: Pubkey
        count: u64

    @instruction
    def initialize(self, authority: Signer):
        self.counter.authority = authority
        self.counter.count = 0

    @instruction
    def increment(self):
        assert self.counter.count >= 0, "Count cannot be negative"
        self.counter.count += 1
