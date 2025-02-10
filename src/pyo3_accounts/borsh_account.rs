use borsh::{BorshDeserialize, BorshSerialize};
use borsh_derive::{BorshSerialize, BorshDeserialize};
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

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
    pub fn serialize(&self) -> PyResult<Vec<u8>> {
        let mut buffer = Vec::new();
        BorshSerialize::serialize(self, &mut buffer)
            .map(|_| buffer)
            .map_err(|e| PyValueError::new_err(format!("Serialization failed: {}", e)))
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

/// Register the Rust module with Python
#[pymodule]
fn dolphin_project(_py: Python,  m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<TokenAccount>()?;
    m.add_class::<Account>()?;
    Ok(())
}