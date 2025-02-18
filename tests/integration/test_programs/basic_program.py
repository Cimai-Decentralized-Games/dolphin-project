
from dolphin.prelude import *

@program("Test111111111111111111111111111111111111111")
class TestProgram:
    @account
    class Counter:
        authority: Pubkey
        count: u64

    @instruction
    def initialize(self, authority: Pubkey):
        self.counter.authority = authority
        self.counter.count = 0

    @instruction
    def increment(self):
        assert self.counter.authority == self.signer
        self.counter.count += 1
