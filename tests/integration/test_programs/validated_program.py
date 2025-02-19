
from dolphin.prelude import *

@program("Test222222222222222222222222222222222222222")
class ValidatedProgram:
    @account
    class ValidatedAccount:
        owner: Pubkey
        data: Vec<u64>
        settings: Option<Pubkey>

    @instruction
    def initialize(self, owner: Signer):
        self.account.owner = owner
