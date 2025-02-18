
from dolphin.prelude import *

@program("Test444444444444444444444444444444444444444")
class TestProgram:
    @account
    class Counter:
        count: u64

    @instruction
    def increment(self):
        self.counter.count += 1
