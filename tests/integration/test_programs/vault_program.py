from dolphin.prelude import *

@program("Vault222222222222222222222222222222222222222")
class VaultProgram:
    @account
    class Vault:
        authority: Pubkey
        balance: u64

    @instruction
    def initialize_vault(self, authority: Pubkey):
        self.vault.authority = authority
        self.vault.balance = 0

    @instruction
    def deposit(self, amount: u64):
        assert self.vault.authority == self.signer
        self.vault.balance += amount

    @instruction
    def withdraw(self, amount: u64):
        assert self.vault.authority == self.signer
        assert self.vault.balance >= amount
        self.vault.balance -= amount