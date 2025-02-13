// src/compiler/validation/accounts.rs
use super::super::generator::accounts::AccountDefinition;

pub fn validate_account_definition(account: &AccountDefinition) -> Result<(), String> {
    // Validate account name
    if !is_valid_rust_identifier(&account.name) {
        return Err(format!("Invalid account name: {}", account.name));
    }
    
    // Validate fields
    for field in &account.fields {
        if !is_valid_rust_identifier(&field.name) {
            return Err(format!("Invalid field name: {}", field.name));
        }
        if !is_valid_rust_type(&field.ty) {
            return Err(format!("Invalid field type: {}", field.ty));
        }
    }
    
    Ok(())
}

fn is_valid_rust_identifier(name: &str) -> bool {
    if name.is_empty() {
        return false;
    }
    
    let first_char = name.chars().next().unwrap();
    if !first_char.is_ascii_alphabetic() && first_char != '_' {
        return false;
    }
    
    name.chars().all(|c| c.is_ascii_alphanumeric() || c == '_')
}

fn is_valid_rust_type(ty: &str) -> bool {
    // Add more sophisticated type validation here
    !ty.is_empty()
}