// src/utils/validation.rs
use pyo3::prelude::*;
use bs58;
use regex::Regex;
use lazy_static::lazy_static;

lazy_static! {
    static ref IDENTIFIER_RE: Regex = Regex::new(r"^[a-zA-Z_][a-zA-Z0-9_]*$").unwrap();
    static ref TYPE_NAME_RE: Regex = Regex::new(r"^[A-Z][a-zA-Z0-9]*$").unwrap();
}

// #[pymodule]
// fn validation(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
//     m.add_function(wrap_pyfunction!(validate_pubkey, m)?)?;
//     m.add_function(wrap_pyfunction!(validate_identifier, m)?)?;
//     m.add_function(wrap_pyfunction!(validate_type_name, m)?)?;
//     m.add_function(wrap_pyfunction!(validate_program_id, m)?)?;
//     Ok(())
// }

#[pyfunction]
pub fn validate_pubkey(key: &str) -> bool {
    if key.len() != 44 && key.len() != 43 {
        return false;
    }

    match bs58::decode(key).into_vec() {
        Ok(bytes) => bytes.len() == 32,
        Err(_) => false,
    }
}

#[pyfunction]
pub fn validate_identifier(name: &str) -> bool {
    IDENTIFIER_RE.is_match(name)
}

#[pyfunction]
pub fn validate_type_name(name: &str) -> bool {
    TYPE_NAME_RE.is_match(name)
}

#[pyfunction]
pub fn validate_program_id(program_id: &str) -> bool {
    validate_pubkey(program_id)
}

#[pyfunction]
pub fn derive_program_address(seeds: Vec<Vec<u8>>, program_id: &str) -> String {
    use solana_program::pubkey::Pubkey;
    use std::str::FromStr;
    
    let program_pubkey = Pubkey::from_str(program_id).unwrap_or_default();
    let seed_slices: Vec<&[u8]> = seeds.iter().map(|v| v.as_slice()).collect();
    Pubkey::create_program_address(seed_slices.as_slice(), &program_pubkey)
        .unwrap_or_default()
        .to_string()
}

#[pyfunction]
pub fn find_program_address(seeds: Vec<Vec<u8>>, program_id: &str) -> (String, u8) {
    use solana_program::pubkey::Pubkey;
    use std::str::FromStr;
    
    let program_pubkey = Pubkey::from_str(program_id).unwrap_or_default();
    let seed_slices: Vec<&[u8]> = seeds.iter().map(|v| v.as_slice()).collect();
    let (pda, bump) = Pubkey::find_program_address(seed_slices.as_slice(), &program_pubkey);
    (pda.to_string(), bump)
}

pub fn validate_account_name(name: &str) -> bool {
    TYPE_NAME_RE.is_match(name)
}

pub fn validate_field_name(name: &str) -> bool {
    IDENTIFIER_RE.is_match(name) && !name.contains(char::is_uppercase)
}

pub fn validate_instruction_name(name: &str) -> bool {
    IDENTIFIER_RE.is_match(name) && !name.contains(char::is_uppercase)
}

pub fn validate_solana_type(type_name: &str) -> bool {
    const VALID_TYPES: &[&str] = &[
        "u8", "u16", "u32", "u64",
        "i8", "i16", "i32", "i64",
        "bool", "String", "Pubkey",
        "Vec<u8>", "Option", "Result",
    ];

    if VALID_TYPES.contains(&type_name) {
        return true;
    }

    if type_name.starts_with("Vec<") && type_name.ends_with(">") {
        let inner_type = &type_name[4..type_name.len()-1];
        return validate_solana_type(inner_type);
    }

    TYPE_NAME_RE.is_match(type_name)
}

#[derive(Debug, thiserror::Error)]
#[pyclass]
pub enum ValidationError {
    #[error("Invalid public key format: {0}")]
    InvalidPubkey(String),
    
    #[error("Invalid identifier name: {0}")]
    InvalidIdentifier(String),
    
    #[error("Invalid type name: {0}")]
    InvalidTypeName(String),
    
    #[error("Invalid program ID: {0}")]
    InvalidProgramId(String),
    
    #[error("Invalid account name: {0}")]
    InvalidAccountName(String),
    
    #[error("Invalid field name: {0}")]
    InvalidFieldName(String),
    
    #[error("Invalid instruction name: {0}")]
    InvalidInstructionName(String),
    
    #[error("Invalid Solana type: {0}")]
    InvalidSolanaType(String),
}

pub fn validate_account(account: &crate::compiler::ir::Account) -> Result<(), ValidationError> {
    if !validate_account_name(&account.name) {
        return Err(ValidationError::InvalidAccountName(account.name.clone()));
    }

    for field in &account.fields {
        if !validate_field_name(&field.name) {
            return Err(ValidationError::InvalidFieldName(field.name.clone()));
        }
        if !validate_solana_type(&field.ty) {
            return Err(ValidationError::InvalidSolanaType(field.ty.clone()));
        }
    }

    Ok(())
}

pub fn validate_instruction(instruction: &crate::compiler::ir::Instruction) -> Result<(), ValidationError> {
    if !validate_instruction_name(&instruction.name) {
        return Err(ValidationError::InvalidInstructionName(instruction.name.clone()));
    }

    for arg in &instruction.arguments {
        if !validate_identifier(&arg.name) {
            return Err(ValidationError::InvalidIdentifier(arg.name.clone()));
        }
        if !validate_solana_type(&arg.ty) {
            return Err(ValidationError::InvalidSolanaType(arg.ty.clone()));
        }
    }

    Ok(())
}

pub fn register(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(validate_pubkey, m)?)?;
    m.add_function(wrap_pyfunction!(validate_identifier, m)?)?;
    m.add_function(wrap_pyfunction!(validate_type_name, m)?)?;
    m.add_function(wrap_pyfunction!(validate_program_id, m)?)?;
    m.add_function(wrap_pyfunction!(derive_program_address, m)?)?;
    m.add_function(wrap_pyfunction!(find_program_address, m)?)?;
    
    // Register ValidationError enum
    m.add_class::<ValidationError>()?;
    
    Ok(())
}
