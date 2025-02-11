pub mod account;
pub mod owner_account;
pub mod borsh_account;

pub use borsh_account::*;
use pyo3::prelude::*;
use pyo3::types::PyModule;

#[pymodule]
pub fn pyo3_accounts(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    let borsh_account_mod = PyModule::new(py, "borsh_account")?;
    borsh_account::register(py, &borsh_account_mod)?;
    
    // Add the borsh_account module to sys.modules
    py.import("sys")?
        .getattr("modules")?
        .set_item("dolphin_project.pyo3_accounts.borsh_account", borsh_account_mod.clone())?;
    
    m.add_submodule(&borsh_account_mod)?;
    Ok(())
}
