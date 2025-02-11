import dolphin_project.pyo3_accounts.borsh_account as borsh_account

class IRGenerator:
    def __init__(self):
        self.accounts = []

    def generate_account(self, mint, owner, amount):
        token_account = borsh_account.TokenAccount(
            mint=mint, 
            owner=owner, 
            amount=amount
        )
        account = borsh_account.Account(
            lamports=5000, 
            owner=owner, 
            token_account=token_account
        )
        self.accounts.append(account)
        return account

    def serialize_accounts(self):
        return [acc.deserialize_data() for acc in self.accounts]

ir_gen = IRGenerator()
test_account = ir_gen.generate_account("Mint123", "OwnerABC", 100)
print("Generated Account:", test_account.deserialize_data())
