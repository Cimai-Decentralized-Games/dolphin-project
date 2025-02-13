// src/lib.rs
use pyo3::prelude::*;

mod compiler;
mod python;
mod utils;

// Be explicit about which register functions we're using
use compiler::generator::accounts::register as register_accounts;
use compiler::generator::instructions::register as register_instructions;
use compiler::generator::programs::register as register_programs;
use utils::validation::register as register_validation;

use compiler::DolphinCompiler;
use python::bindings::{AccountGenerator, ProgramGenerator, InstructionGenerator};

#[pymodule]
fn dolphin(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Register the compiler
    m.add_class::<DolphinCompiler>()?;

    // Add validation submodule
    let validation_module: Bound<'_, PyModule> = PyModule::new(py, "validation")?;
    register_validation(py, &validation_module)?;
    m.add_submodule(&validation_module)?;

    // Add generator submodule
    let generator_module: Bound<'_, PyModule> = PyModule::new(py, "generator")?;
    register_accounts(py, &generator_module)?;
    register_instructions(py, &generator_module)?;
    register_programs(py, &generator_module)?;
    m.add_submodule(&generator_module)?;

    // Register remaining types
    m.add_class::<AccountGenerator>()?;
    m.add_class::<ProgramGenerator>()?;
    m.add_class::<InstructionGenerator>()?;

    // Add PDA functions
    m.add_function(wrap_pyfunction!(utils::pda::create_program_address, m)?)?;
    m.add_function(wrap_pyfunction!(utils::pda::find_program_address, m)?)?;

    // Add version info
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_wrapped(wrap_pyfunction!(version))?;

    Ok(())
}

#[pyfunction]
fn version() -> String {
    format!(
        "Dolphin v{} ({})",
        env!("CARGO_PKG_VERSION"),
        env!("CARGO_PKG_AUTHORS")
    )
}

// Re-export key types for internal use
pub use compiler::ir::{
    IR,
    Account,
    Instruction,
    AccountUsage,
    Statement,
    Expression,
    CustomType,
};

pub use utils::validation::{
    ValidationError,
    validate_pubkey,
    validate_program_id,
    validate_identifier,
    validate_type_name,
};

