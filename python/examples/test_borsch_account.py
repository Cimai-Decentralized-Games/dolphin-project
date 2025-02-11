# python/examples/test_borsch_account.py
from dolphin_project.pyo3_accounts import borsh_account

def test_python_integration():
    print("Creating TokenAccount...")
    token_account = borsh_account.TokenAccount(
        mint="MintAddress123",
        owner="OwnerAddress456",
        amount=1000
    )
    print(f"TokenAccount created:")
    print(f"  Mint: {token_account.mint}")
    print(f"  Owner: {token_account.owner}")
    print(f"  Amount: {token_account.amount}")

    print("\nCreating Account...")
    account = borsh_account.Account(
        lamports=5000,
        owner="OwnerAddress456",
        token_account=token_account  # Pass TokenAccount instance
    )
    print(f"Account created:")
    print(f"  Lamports: {account.lamports}")
    print(f"  Owner: {account.owner}")

    print("\nSerializing and Deserializing...")
    deserialized = account.deserialize_data()
    
    print("Deserialized TokenAccount details:")
    print(f"  Mint: {deserialized.mint}")
    print(f"  Owner: {deserialized.owner}")
    print(f"  Amount: {deserialized.amount}")

    print("\nRunning assertions...")
    assert deserialized.mint == "MintAddress123", "Mint mismatch"
    assert deserialized.owner == "OwnerAddress456", "Owner mismatch"
    assert deserialized.amount == 1000, "Amount mismatch"

    print("\n✅ Python integration test PASSED successfully!")

if __name__ == "__main__":
    test_python_integration()
