import test_lib_borsch_account

def test_python_integration():
    token_account = test_lib_borsch_account.TokenAccount(
        mint="MintAddress123",
        owner="OwnerAddress456",
        amount=1000
    )

    account = test_lib_borsch_account.Account(
        lamports=5000,
        owner="OwnerAddress456",
        token_account=token_account
    )

    deserialized = account.deserialize_data()
    
    assert deserialized.mint == "MintAddress123"
    assert deserialized.owner == "OwnerAddress456"
    assert deserialized.amount == 1000

    print("Python test passed!")

if __name__ == "__main__":
    test_python_integration()
