from dolphin_project.pyo3_accounts import borsh_account

def test_python_integration():
    print("Creating TokenAccount...")
    # Using valid Solana-like addresses
    token_account = borsh_account.TokenAccount(
        mint="8e7ekBeWmMdU6sJqnCwhm3P2bHBpNwZZ6RNiWJyrMyYz",
        owner="2vp6JLrKvwhMMokuNAASReGsiNNwDD86gTB1uiN2hKS8",
        amount=1000,
        decimals=9
    )
    print(f"TokenAccount created:")
    print(f"  Mint: {token_account.mint}")
    print(f"  Owner: {token_account.owner}")
    print(f"  Amount: {token_account.amount}")
    print(f"  Decimals: {token_account.decimals}")
    print(f"  Is Frozen: {token_account.is_frozen}")

    print("\nTesting token operations...")
    # Test deposit
    token_account.deposit(500)
    assert token_account.amount == 1500, "Deposit failed"
    
    # Test withdraw
    token_account.withdraw(200)
    assert token_account.amount == 1300, "Withdraw failed"
    
    # Test freeze/thaw
    token_account.freeze()
    assert token_account.is_frozen == True, "Freeze failed"
    token_account.thaw()
    assert token_account.is_frozen == False, "Thaw failed"

    print("\nCreating Account...")
    account = borsh_account.Account(
        lamports=1_000_000,
        owner="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",  # Using a valid Solana-like address
        token_account=token_account
    )
    print(f"Account created:")
    print(f"  Lamports: {account.lamports}")
    print(f"  Owner: {account.owner}")
    
    # Get account hash
    account_hash = account.hash()
    print(f"  Account Hash: {account_hash}")

    print("\nSerializing and Deserializing...")
    deserialized = account.deserialize_data()
    
    print("Deserialized TokenAccount details:")
    print(f"  Mint: {deserialized.mint}")
    print(f"  Owner: {deserialized.owner}")
    print(f"  Amount: {deserialized.amount}")
    print(f"  Decimals: {deserialized.decimals}")
    print(f"  Is Frozen: {deserialized.is_frozen}")

    print("\nRunning assertions...")
    assert deserialized.mint == "8e7ekBeWmMdU6sJqnCwhm3P2bHBpNwZZ6RNiWJyrMyYz", "Mint mismatch"
    assert deserialized.owner == "2vp6JLrKvwhMMokuNAASReGsiNNwDD86gTB1uiN2hKS8", "Owner mismatch"
    assert deserialized.amount == 1300, "Amount mismatch"
    assert deserialized.decimals == 9, "Decimals mismatch"
    assert deserialized.is_frozen == False, "Frozen state mismatch"

    print("\nTesting error cases...")
    try:
        # Test invalid mint address
        borsh_account.TokenAccount(
            mint="InvalidAddress",
            owner="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            amount=1000,
            decimals=9
        )
        assert False, "Should have raised error for invalid mint address"
    except ValueError as e:
        print(f"  ✓ Successfully caught invalid mint address: {e}")

    try:
        # Test insufficient lamports
        borsh_account.Account(
            lamports=100,
            owner="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            token_account=token_account
        )
        assert False, "Should have raised error for insufficient lamports"
    except ValueError as e:
        print(f"  ✓ Successfully caught insufficient lamports: {e}")

    print("\n✅ Python integration test PASSED successfully!")

if __name__ == "__main__":
    test_python_integration()
