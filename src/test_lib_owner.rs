use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use std::hash::Hash;
use pyo3::class::basic::CompareOp;
use pyo3::types::PyModule;
use pyo3::{PyAny, Python, PyResult, Py};
use reqwest;
use serde_json::Value;



// Helper function for u64 handling
fn wrap_u64(obj: &Bound<'_, PyAny>) -> PyResult<u64> {
    let val = obj.call_method1("__and__", (0xFFFFFFFFFFFFFFFF_u64,))?;
    let val: u64 = val.extract()?;
    Ok(val)
}

// Define the Owner class
#[pyclass]
#[derive(Clone, PartialEq, Eq, Hash)]
struct Owner {
    #[pyo3(get, set)]
    name: String,
}

#[pymethods]
impl Owner {
    #[new]
    fn new(name: String) -> Self {
        Owner { name }
    }

    fn __repr__(&self) -> String {
        format!("Owner({})", self.name)
    }
}

// Define the Account class
#[pyclass]
// #[derive(Clone, PartialEq, Eq, Hash)]
struct Account {
    #[pyo3(get, set)]
    lamports: u64,
    #[pyo3(get, set)]
    data: Vec<u8>,
    owner: Py<Owner>, // Py<Owner> instead of direct Owner
}

#[pymethods]
impl Account {
    #[new]
    fn new(
        #[pyo3(from_py_with = "wrap_u64")] lamports: u64, 
        data: Vec<u8>, 
        owner: Py<Owner> // Accept Py<Owner> 
    ) -> Self {
        Account { lamports, data, owner }
    }

    fn __repr__(&self, py: Python) -> String {
        let owner_ref = self.owner.borrow(py); // ✅ Get the reference safely
        format!(
            "Account(lamports={}, data_len={}, owner={})",
            self.lamports, self.data.len(), owner_ref.name
        )
    }

    fn __len__(&self) -> usize {
        self.data.len()
    }

    fn __bool__(&self) -> bool {
        self.lamports > 0
    }

    fn __richcmp__(&self, other: &Self, op: CompareOp) -> bool {
        match op {
            CompareOp::Lt => self.lamports < other.lamports,
            CompareOp::Le => self.lamports <= other.lamports,
            CompareOp::Eq => self.lamports == other.lamports,
            CompareOp::Ne => self.lamports != other.lamports,
            CompareOp::Gt => self.lamports > other.lamports,
            CompareOp::Ge => self.lamports >= other.lamports,
        }
    }

    fn update_data(&mut self, new_data: Vec<u8>) -> PyResult<()> {
        if new_data.len() > 1024 {
            return Err(PyValueError::new_err("Data too large"));
        }
        self.data = new_data;
        Ok(())
    }

    fn set_owner(&mut self, new_owner: Py<Owner>) {
        self.owner = new_owner;
    }
}

// Define Signer class
#[pyclass]
#[derive(Clone)]
struct Signer {}

#[pymethods]
impl Signer {
    #[new]
    fn new() -> Self {
        Signer {}
    }

    #[getter] // ✅ Expose as a property
    fn key(&self) -> String {
        "SignerKey".to_string()
    }
}

// Define Program class
#[pyclass]
#[derive(Clone)]
struct Program {}

#[pymethods]
impl Program {
    #[new]
    fn new() -> Self {
        Program {}
    }

    fn invoke(&self) -> String {
        "ProgramInvoked".to_string()
    }

    #[getter] // ✅ Expose as a property
    fn key(&self) -> String {
        "ProgramKey".to_string()
    }
}

#[pyclass]
#[derive(Clone)]
struct Clock {}

#[pymethods]
impl Clock {
    #[new]
    fn new() -> Self {
        Clock {}
    }

    fn slot(&self) -> PyResult<u64> {
        Self::fetch_slot().map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    fn epoch(&self) -> PyResult<u64> {
        Self::fetch_epoch().map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    fn unix_timestamp(&self) -> PyResult<i64> {
        Self::fetch_unix_timestamp().map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
}

impl Clock {
    fn fetch_slot() -> Result<u64, Box<dyn std::error::Error>> {
        let client = reqwest::blocking::Client::new();
        let res: Value = client
            .post("https://api.mainnet-beta.solana.com")
            .header("Content-Type", "application/json")
            .body(r#"{"jsonrpc":"2.0","id":1,"method":"getSlot"}"#)
            .send()?
            .json()?;

        Ok(res["result"].as_u64().unwrap_or(0))
    }

    fn fetch_epoch() -> Result<u64, Box<dyn std::error::Error>> {
        let client = reqwest::blocking::Client::new();
        let res: Value = client
            .post("https://api.mainnet-beta.solana.com")
            .header("Content-Type", "application/json")
            .body(r#"{"jsonrpc":"2.0","id":1,"method":"getEpochInfo"}"#)
            .send()?
            .json()?;

        Ok(res["result"]["epoch"].as_u64().unwrap_or(0))
    }

    fn fetch_unix_timestamp() -> Result<i64, Box<dyn std::error::Error>> {
        let latest_slot = Self::fetch_slot()?; // Get latest slot first
        let client = reqwest::blocking::Client::new();
        let res: Value = client
            .post("https://api.mainnet-beta.solana.com")
            .header("Content-Type", "application/json")
            .body(format!(r#"{{"jsonrpc":"2.0","id":1,"method":"getBlockTime","params":[{}]}}"#, latest_slot))
            .send()?
            .json()?;

        Ok(res["result"].as_i64().unwrap_or(0))
    }
}

// Define Key class
#[pyclass]
#[derive(Clone)]
struct Key {}

#[pymethods]
impl Key {
    #[new]
    fn new() -> Self {
        Key {}
    }
}

// Define Empty class
#[pyclass]
struct Empty {}

#[pymethods]
impl Empty {
    #[new]
    fn new() -> Self {
        Empty {}
    }
}

// Python module definition
#[pymodule]
fn dolphin_project(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Owner>()?;   // Add Owner class
    m.add_class::<Account>()?;
    m.add_class::<Signer>()?;
    m.add_class::<Program>()?;
    m.add_class::<Clock>()?;
    m.add_class::<Key>()?;
    m.add_class::<Empty>()?;
    Ok(())
}
