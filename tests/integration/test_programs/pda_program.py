
    from dolphin.prelude import *

    @program("Test333333333333333333333333333333333333333")
    class PDAProgram:
        @account
        @pda(seeds=["vault", "mint"])  # Use proper PDA seeds
        class TokenVault:
            mint: Pubkey     # Mint address as seed
            amount: u64      # Vault balance
            bump: u8         # Store bump for derivation

        @instruction
        def initialize(self, mint: Pubkey, bump: u8):
            self.token_vault.mint = mint
            self.token_vault.amount = 0
            self.token_vault.bump = bump
    