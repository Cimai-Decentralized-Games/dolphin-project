
from dolphin.prelude import *

@program("Test222222222222222222222222222222222222222")
class TestProgram:
    @account
    @pda("owner", "mint")
    class TokenAccount:
        owner: Pubkey
        mint: Pubkey
        amount: u64

    @instruction
    def initialize(self, owner: Pubkey, mint: Pubkey):
        self.token_account.owner = owner
        self.token_account.mint = mint
        self.token_account.amount = 0
