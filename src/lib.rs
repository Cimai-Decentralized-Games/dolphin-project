use pyo3::prelude::*;
use pyo3::types::PyModule;

pub mod pyo3_accounts;

#[pymodule]
fn dolphin_project(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    let pyo3_accounts_mod = PyModule::new(py, "pyo3_accounts")?;
    pyo3_accounts::pyo3_accounts(py, &pyo3_accounts_mod)?;
    
    // Add the module to sys.modules to make it importable
    py.import("sys")?
        .getattr("modules")?
        .set_item("dolphin_project.pyo3_accounts", pyo3_accounts_mod.clone())?;
    
    m.add_submodule(&pyo3_accounts_mod)?;
    Ok(())
}

// pub mod pyo3_accounts;

// use pyo3::prelude::*;

// #[pymodule]
// fn dolphin_project(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
//     // Create and register the `pyo3_accounts` submodule
//     let pyo3_accounts_module = PyModule::new(py, "pyo3_accounts")?;
//     pyo3_accounts::borsh_account::register(py, &pyo3_accounts_module)?;
//     m.add_submodule(&pyo3_accounts_module)?;

//     Ok(())
// }
