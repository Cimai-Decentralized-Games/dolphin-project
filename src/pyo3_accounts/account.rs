use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use std::hash::Hash;
use pyo3::class::basic::CompareOp;
use pyo3::types::PyModule;
use pyo3::{PyAny, Python, PyResult};

fn wrap_u64(obj: &Bound<'_, PyAny>) -> PyResult<u64> {
    let val = obj.call_method1("__and__", (0xFFFFFFFFFFFFFFFF_u64,))?;
    let val: u64 = val.extract()?;
    Ok(val)
}

#[pyclass]
#[derive(Clone, PartialEq, Eq, Hash)]
struct Account {
    #[pyo3(get, set)]
    lamports: u64,
    #[pyo3(get, set)]
    data: Vec<u8>,
    #[pyo3(get, set)]
    owner: String, // Let's assume this is a string for simplicity
}

#[pymethods]
impl Account {
    #[new]
    fn new(#[pyo3(from_py_with = "wrap_u64")] lamports: u64, data: Vec<u8>, owner: String) -> Self {
        Account { lamports, data, owner }
    }

    fn __repr__(&self) -> String {
        format!("Account(lamports={}, data_len={}, owner={})", self.lamports, self.data.len(), self.owner)
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
            CompareOp::Eq => self == other,
            CompareOp::Ne => self != other,
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
}

#[pyclass]
#[derive(Clone)]
struct Signer {
}

#[pymethods]
impl Signer{
    #[new]
    fn new() -> Self{
        Signer{}
    }
    fn key(&self) -> String {
        "SignerKey".to_string()
    }
}

#[pyclass]
#[derive(Clone)]
struct Program{
}

#[pymethods]
impl Program{
    #[new]
    fn new() -> Self {
        Program{}
    }

    fn invoke(&self) -> String{
        "ProgramInvoked".to_string()
    }

    fn key(&self) -> String {
        "ProgramKey".to_string()
    }
}

#[pyclass]
#[derive(Clone)]
struct Clock{
}

#[pymethods]
impl Clock{
    #[new]
    fn new() -> Self{
        Clock{}
    }

    fn slot(&self) -> u64{
        10
    }

    fn epoch(&self) -> u64{
        20
    }

    fn unix_timestamp(&self) -> i64{
        30
    }
}

#[pyclass]
#[derive(Clone)]
struct Key{
}

#[pymethods]
impl Key{
    #[new]
    fn new() -> Self{
        Key{}
    }
}

#[pyclass]
struct Empty{
}

#[pymethods]
impl Empty{
    #[new]
    fn new() -> Self{
        Empty{}
    }
}


#[pymodule]
fn dolphin_project_account(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Account>()?;
    m.add_class::<Signer>()?;
    m.add_class::<Program>()?;
    m.add_class::<Clock>()?;
    m.add_class::<Key>()?;
    m.add_class::<Empty>()?;
    Ok(())
}
