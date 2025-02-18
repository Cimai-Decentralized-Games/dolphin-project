
from dolphin.prelude import *

@program("Test333333333333333333333333333333333333333")
class TestProgram:
    @account
    class InvalidAccount:
        # Invalid type
        balance: invalid_type

    @instruction
    def initialize(self):
        pass
