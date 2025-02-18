// src/utils/pda.rs
use pyo3::prelude::*;
use solana_program::pubkey::Pubkey;
use solana_program::hash::hash;
use std::str::FromStr;

#[pyfunction]
pub fn create_program_address(seeds: Vec<Vec<u8>>, program_id: &str) -> PyResult<String> {
    let program_pubkey = Pubkey::from_str(program_id)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    match Pubkey::create_program_address(&seeds.iter().map(|s| &s[..]).collect::<Vec<&[u8]>>(), &program_pubkey) {
        Ok(pubkey) => Ok(pubkey.to_string()),
        Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }
}

#[pyfunction]
pub fn find_program_address(seeds: Vec<Vec<u8>>, program_id: &str) -> PyResult<(String, u8)> {
    let program_pubkey = Pubkey::from_str(program_id)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    let (pubkey, bump) = Pubkey::find_program_address(
        &seeds.iter().map(|s| &s[..]).collect::<Vec<&[u8]>>(),
        &program_pubkey
    );

    Ok((pubkey.to_string(), bump))
}