// src/compiler/templates/accounts.rs
use pyo3::prelude::*;


pub const TOKEN_ACCOUNT_TEMPLATE: &str = r#"
#[pyclass]
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[account]
pub struct TokenAccount {
    pub mint: Pubkey,
    pub owner: Pubkey,
    pub amount: u64,
    pub decimals: u8,
    pub is_frozen: bool,
}
"#;

pub const MINT_ACCOUNT_TEMPLATE: &str = r#"
#[pyclass]
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[account]
pub struct Mint {
    pub mint_authority: Pubkey,
    pub supply: u64,
    pub decimals: u8,
    pub is_initialized: bool,
    pub freeze_authority: Option<Pubkey>,
}
"#;