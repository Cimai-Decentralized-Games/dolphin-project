"""
Token Program Example
This example demonstrates a simple token program with minting and transfers
"""
from dolphin.prelude import *

@program("TokenProg2222222222222222222222222222222222222")
class TokenProgram:
    @account
    class TokenMint:
        authority: Pubkey
        supply: u64
        decimals: u8

    @account
    @pda("owner", "mint")
    class TokenAccount:
        owner: Pubkey
        mint: Pubkey
        amount: u64

    @instruction
    def initialize_mint(self, authority: Pubkey, decimals: u8):
        """Initialize a new token mint"""
        self.mint.authority = authority
        self.mint.supply = 0
        self.mint.decimals = decimals

    @instruction
    def mint_to(self, amount: u64):
        """Mint tokens to an account"""
        assert self.mint.authority == self.signer, "Only mint authority can mint"
        
        self.token_account.amount += amount
        self.mint.supply += amount

    @instruction
    def transfer(self, amount: u64, to_account: TokenAccount):
        """Transfer tokens between accounts"""
        assert self.token_account.owner == self.signer, "Only owner can transfer"
        assert self.token_account.amount >= amount, "Insufficient funds"
        assert self.token_account.mint == to_account.mint, "Mints must match"

        self.token_account.amount -= amount
        to_account.amount += amount