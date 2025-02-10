use borsh::{BorshDeserialize, BorshSerialize};
use dolphin_project::pyo3_accounts::borsh_account::{Account, TokenAccount};

#[test]
fn test_token_account_serialization() {
    let token_account = TokenAccount {
        mint: "MintAddress123".to_string(),
        owner: "OwnerAddress456".to_string(),
        amount: 1000,
    };

    let serialized = token_account.serialize().expect("Serialization failed");
    let deserialized = TokenAccount::deserialize(&mut &serialized[..]).expect("Deserialization failed");

    assert_eq!(token_account.mint, deserialized.mint);
    assert_eq!(token_account.owner, deserialized.owner);
    assert_eq!(token_account.amount, deserialized.amount);
}

#[test]
fn test_account_serialization() {
    let token_account = TokenAccount {
        mint: "MintAddress123".to_string(),
        owner: "OwnerAddress456".to_string(),
        amount: 1000,
    };

    let account = Account::new(5000, "OwnerAddress456".to_string(), token_account).expect("Account creation failed");
    let deserialized_account = account.deserialize_data().expect("Deserialization failed");

    assert_eq!(deserialized_account.mint, "MintAddress123");
    assert_eq!(deserialized_account.owner, "OwnerAddress456");
    assert_eq!(deserialized_account.amount, 1000);
}