use dolphin::serialization::{serialize_instruction, deserialize_account};
use solana_program::pubkey::Pubkey;

#[test]
fn test_instruction_serialization() {
    let instruction_data = InstructionData {
        name: "initialize".to_string(),
        args: vec![
            ("authority".to_string(), ProgramValue::Pubkey(Pubkey::new_unique())),
            ("amount".to_string(), ProgramValue::U64(100))
        ]
    };
    
    let serialized = serialize_instruction(&instruction_data);
    assert!(serialized.is_ok());
    
    let bytes = serialized.unwrap();
    assert!(!bytes.is_empty());
}

#[test]
fn test_account_deserialization() {
    let account_data = vec![
        0, 0, 0, 0,  // Discriminator
        1, 0, 0, 0, 0, 0, 0, 0,  // u64 value
        // ... more test data ...
    ];
    
    let result = deserialize_account::<TestAccount>(&account_data);
    assert!(result.is_ok());
}

#[test]
fn test_invalid_account_data() {
    let invalid_data = vec![1, 2, 3];  // Too short
    
    let result = deserialize_account::<TestAccount>(&invalid_data);
    assert!(result.is_err());
}