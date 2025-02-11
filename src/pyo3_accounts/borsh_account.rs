use borsh::{BorshDeserialize, BorshSerialize};
use borsh_derive::{BorshSerialize, BorshDeserialize};
use pyo3::prelude::*;
use pyo3::exceptions::{PyValueError, PyOverflowError};
use pyo3::types::PyType;
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

const MIN_ACCOUNT_LAMPORTS: u64 = 1_000_000;
const MAX_TOKEN_AMOUNT: u64 = u64::MAX;

pub fn register(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
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
    #[pyo3(get, set)]
    pub decimals: u8,
    #[pyo3(get, set)]
    pub is_frozen: bool,
}

#[pymethods]
impl TokenAccount {
    #[new]
    pub fn new(mint: String, owner: String, amount: u64, decimals: u8) -> PyResult<Self> {
        // Validate inputs using static method
        if !TokenAccount::validate_address(&mint) {
            return Err(PyValueError::new_err("Invalid mint address"));
        }
        if !TokenAccount::validate_address(&owner) {
            return Err(PyValueError::new_err("Invalid owner address"));
        }

        Ok(TokenAccount {
            mint,
            owner,
            amount,
            decimals,
            is_frozen: false,
        })
    }

    #[staticmethod]
    pub fn validate_address(address: &str) -> bool {
        // Basic length check for base58 encoded public key
        if address.len() < 32 || address.len() > 44 {
            return false;
        }

        // Check if the address only contains valid base58 characters
        address.chars().all(|c| {
            c.is_ascii_alphanumeric() && !c.is_ascii_whitespace() && c != 'O' && c != 'I' && c != 'l'
        })
    }


    pub fn deposit(&mut self, amount: u64) -> PyResult<()> {
        self.amount = self.amount
            .checked_add(amount)
            .ok_or_else(|| PyOverflowError::new_err("Token amount overflow"))?;
        
        if self.amount > MAX_TOKEN_AMOUNT {
            return Err(PyValueError::new_err("Exceeds maximum token amount"));
        }
        Ok(())
    }

    pub fn withdraw(&mut self, amount: u64) -> PyResult<()> {
        if self.is_frozen {
            return Err(PyValueError::new_err("Account is frozen"));
        }

        self.amount = self.amount
            .checked_sub(amount)
            .ok_or_else(|| PyValueError::new_err("Insufficient funds"))?;
        Ok(())
    }

    pub fn transfer(&mut self, to_account: &mut TokenAccount, amount: u64) -> PyResult<()> {
        if self.is_frozen || to_account.is_frozen {
            return Err(PyValueError::new_err("One of the accounts is frozen"));
        }

        if self.mint != to_account.mint {
            return Err(PyValueError::new_err("Mint addresses don't match"));
        }

        self.withdraw(amount)?;
        to_account.deposit(amount)?;
        Ok(())
    }

    pub fn freeze(&mut self) -> PyResult<()> {
        self.is_frozen = true;
        Ok(())
    }

    pub fn thaw(&mut self) -> PyResult<()> {
        self.is_frozen = false;
        Ok(())
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
        // Use the same validation method from TokenAccount
        if !TokenAccount::validate_address(&owner) {
            return Err(PyValueError::new_err("Invalid owner address"));
        }

        // Validate minimum lamports
        if lamports < MIN_ACCOUNT_LAMPORTS {
            return Err(PyValueError::new_err("Insufficient lamports for account creation"));
        }

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
