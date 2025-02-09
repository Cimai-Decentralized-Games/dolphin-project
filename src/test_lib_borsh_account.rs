use borsh::{BorshDeserialize, BorshSerialize};
use pyo3::prelude::*;

// Helper function for u64 handling
fn wrap_u64(obj: &Bound<'_, PyAny>) -> PyResult<u64> {
    let val = obj.call_method1("__and__", (0xFFFFFFFFFFFFFFFF_u64,))?;
    let val: u64 = val.extract()?;
    Ok(val)
}

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct TokenAccount {
    pub mint: String, // Token mint address
    pub owner: String, // Owner of the account
    pub amount: u64, // Token balance
}

#[pyclass]
pub struct Account {
    pub lamports: u64,
    pub data: Vec<u8>,  // Serialized TokenAccount data
    pub owner: String,  // Owner address
}

#[pymethods]
impl Account {
    #[new]
    pub fn new(lamports: u64, data: Vec<u8>, owner: String) -> Self {
        Account { lamports, data, owner }
    }

    pub fn deserialize_data(&self) -> PyResult<TokenAccount> {
        TokenAccount::try_from_slice(&self.data)
            .map_err(|e| PyValueError::new_err(format!("Failed to deserialize: {}", e)))
    }
}