use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use pyo3::class::basic::CompareOp;

fn wrap_u64(obj: &Bound<'_, PyAny>) -> PyResult<u64> {
    let val = obj.call_method1("__and__", (0xFFFFFFFFFFFFFFFF_u64,))?;
    let val: u64 = val.extract()?;
    Ok(val)
}

#[pyclass(frozen, eq, hash)]
#[derive(Clone, PartialEq, Eq, Hash)]
struct Account {
    #[pyo3(get, set)]
    lamports: u64,
    #[pyo3(get, set)]
    data: Vec<u8>,
    #[pyo3(get)]
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

#[pymodule]
fn dolphin_project(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Account>()?;
    Ok(())
}