# tests/python/test_accounts.py
import dolphin_project
import pytest

def test_token_account_serialization():
    token_account = dolphin_project.TokenAccount(
        mint="MintAddress123",
        owner="OwnerAddress456",
        amount=1000,
    )

    serialized = token_account.serialize()
    deserialized = dolphin_project.TokenAccount.deserialize(serialized)

    assert token_account.mint == deserialized.mint
    assert token_account.owner == deserialized.owner
    assert token_account.amount == deserialized.amount

def test_account_creation():
    token_account = dolphin_project.TokenAccount(
        mint="MintAddress123",
        owner="OwnerAddress456",
        amount=1000,
    )

    account = dolphin_project.Account(
        lamports=5000,
        owner="OwnerAddress456",
        token_account=token_account
    )

    assert account.lamports == 5000
    assert account.owner == "OwnerAddress456"
