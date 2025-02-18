//! Dolphin Framework - A Python-to-Solana Framework
//! 
//! This crate provides the Rust implementation of the Dolphin framework,
//! including the compiler, code generator, and Python bindings.

use pyo3::prelude::*;
use pyo3::types::PyModule;
use pyo3::wrap_pyfunction;

pub mod compiler;
pub mod python;
pub mod utils;

// Register module functions
use compiler::generator::accounts::register as register_accounts;
use compiler::generator::instructions::register as register_instructions;
use compiler::generator::programs::register as register_programs;
use utils::validation::register as register_validation;

// Import core types and generators
use compiler::DolphinCompiler;
use python::bindings::{AccountGenerator, ProgramGenerator, InstructionGenerator};

/// The main Python module for Dolphin
#[pymodule]
fn dolphin(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Register the compiler
    m.add_class::<DolphinCompiler>()?;

    // Add validation submodule
    let validation_module = PyModule::new(py, "validation")?;
    register_validation(py, &validation_module)?;
    m.add_submodule(&validation_module)?;

    // Add generator submodule
    let generator_module = PyModule::new(py, "generator")?;
    
    // Register generator components
    register_accounts(py, &generator_module)?;
    register_instructions(py, &generator_module)?;
    register_programs(py, &generator_module)?;

    // Add generator classes
    generator_module.add_class::<AccountGenerator>()?;
    generator_module.add_class::<ProgramGenerator>()?;
    generator_module.add_class::<InstructionGenerator>()?;

    m.add_submodule(&generator_module)?;

    // Add PDA functions
    m.add_wrapped(wrap_pyfunction!(create_program_address))?;
    m.add_wrapped(wrap_pyfunction!(find_program_address))?;

    // Add utility functions
    m.add_wrapped(wrap_pyfunction!(validate_pubkey))?;
    m.add_wrapped(wrap_pyfunction!(validate_program_id))?;

    // Add version info
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__author__", env!("CARGO_PKG_AUTHORS"))?;
    m.add_wrapped(wrap_pyfunction!(version))?;

    Ok(())
}

/// Get the version string
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

pub use utils::pda::{
    create_program_address,
    find_program_address,
};

// Error types
#[derive(Debug, thiserror::Error)]
pub enum DolphinError {
    #[error("Compilation error: {0}")]
    CompilationError(String),
    
    #[error("Validation error: {0}")]
    ValidationError(#[from] ValidationError),
    
    #[error("Python error: {0}")]
    PythonError(#[from] pyo3::PyErr),
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
}

impl From<DolphinError> for pyo3::PyErr {
    fn from(err: DolphinError) -> Self {
        pyo3::exceptions::PyRuntimeError::new_err(err.to_string())
    }
}

// Test module
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version() {
        let version_str = version();
        assert!(version_str.starts_with("Dolphin v"));
        assert!(version_str.contains(env!("CARGO_PKG_VERSION")));
    }
}
