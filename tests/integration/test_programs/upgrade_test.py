
from dolphin.prelude import *

@program("Test666666666666666666666666666666666666666")
class TestProgram:
    @account
    class Counter:
        count: u64

    @instruction
    def increment(self):
        self.counter.count += 1
