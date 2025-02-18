use dolphin::utils::pda::{create_program_address, find_program_address};
use solana_program::pubkey::Pubkey;
use std::str::FromStr;

#[test]
pub fn test_create_program_address() {
    let program_id = "Test111111111111111111111111111111111111111";
    let seeds = vec![b"test".to_vec(), vec![1, 2, 3]];
    
    let result = create_program_address(seeds, program_id);
    assert!(result.is_ok());
}

#[test]
pub fn test_find_program_address() {
    let program_id = "Test111111111111111111111111111111111111111";
    let seeds = vec![b"test".to_vec(), vec![1, 2, 3]];
    
    let result = find_program_address(seeds, program_id);
    assert!(result.is_ok());
    
    let (pda, bump) = result.unwrap();
    assert!(bump < 255);
}

#[test]
pub fn test_invalid_program_id() {
    let program_id = "invalid";
    let seeds = vec![b"test".to_vec()];
    
    let result = create_program_address(seeds, program_id);
    assert!(result.is_err());
}