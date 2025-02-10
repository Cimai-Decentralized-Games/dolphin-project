import test_lib_borsch_account

class IRGenerator:
    def __init__(self):
        self.accounts = []

    def generate_account(self, mint, owner, amount):
        token_account = test_lib_borsch_account.TokenAccount(mint, owner, amount)
        account = test_lib_borsch_account.Account(lamports=5000, owner=owner, token_account=token_account)
        self.accounts.append(account)
        return account

    def serialize_accounts(self):
        return [acc.deserialize_data() for acc in self.accounts]

ir_gen = IRGenerator()
test_account = ir_gen.generate_account("Mint123", "OwnerABC", 100)
print("Generated Account:", test_account.deserialize_data())
