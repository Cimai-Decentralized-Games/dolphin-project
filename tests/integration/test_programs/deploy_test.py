
from dolphin.prelude import *

@program("Test555555555555555555555555555555555555555")
class TestProgram:
    @account
    class Counter:
        count: u64

    @instruction
    def increment(self):
        self.counter.count += 1
