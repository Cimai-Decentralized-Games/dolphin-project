// src/pyo3_accounts/borsh_account.rs
use borsh::{BorshDeserialize, BorshSerialize};
use borsh_derive::{BorshSerialize, BorshDeserialize};
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::PyType;
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

pub fn register(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Register classes directly in the module
    m.add_class::<TokenAccount>()?;
    m.add_class::<Account>()?;
    Ok(())
}


#[pyclass]
#[derive(BorshSerialize, BorshDeserialize, Debug, Clone)]
pub struct TokenAccount {
    #[pyo3(get, set)]
    pub mint: String,

    #[pyo3(get, set)]
    pub owner: String,

    #[pyo3(get, set)]
    pub amount: u64,
}

#[pymethods]
impl TokenAccount {
    #[new]
    pub fn new(mint: String, owner: String, amount: u64) -> PyResult<Self> {
        Ok(TokenAccount {
            mint,
            owner,
            amount,
        })
    }

    pub fn serialize(&self) -> PyResult<Vec<u8>> {
        let mut buffer = Vec::new();
        BorshSerialize::serialize(self, &mut buffer)
            .map(|_| buffer)
            .map_err(|e| PyValueError::new_err(format!("Serialization failed: {}", e)))
    }

    #[classmethod]
    pub fn deserialize(_cls: &Bound<'_, PyType>, serialized: Vec<u8>) -> PyResult<Self> {
        TokenAccount::try_from_slice(&serialized)
            .map_err(|e| PyValueError::new_err(format!("Failed to deserialize: {}", e)))
    }
}

#[pyclass]
pub struct Account {
    #[pyo3(get, set)]
    pub lamports: u64,

    pub data: Vec<u8>,

    #[pyo3(get, set)]
    pub owner: String,
}

#[pymethods]
impl Account {
    #[new]
    pub fn new(lamports: u64, owner: String, token_account: TokenAccount) -> PyResult<Self> {
        let serialized_data = token_account.serialize()?;

        Ok(Account {
            lamports,
            data: serialized_data,
            owner,
        })
    }

    pub fn deserialize_data(&self) -> PyResult<TokenAccount> {
        TokenAccount::try_from_slice(&self.data)
            .map_err(|e| PyValueError::new_err(format!("Failed to deserialize: {}", e)))
    }

    pub fn hash(&self) -> u64 {
        let mut hasher = DefaultHasher::new();
        self.owner.hash(&mut hasher);
        self.lamports.hash(&mut hasher);
        hasher.finish()
    }
}
