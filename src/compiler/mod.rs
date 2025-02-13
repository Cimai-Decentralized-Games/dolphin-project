// src/compiler/mod.rs
pub mod generator;
pub mod templates;
pub mod validation;
pub mod ir;
pub mod codegen;

use pyo3::prelude::*;
use std::error::Error;
use pyo3::exceptions::PyRuntimeError;
use std::path::PathBuf;
use crate::compiler::generator::{accounts, instructions};
use crate::compiler::ir::IR;

#[pyclass]
#[derive(Debug)]
pub struct DolphinCompiler {
    python_frontend: PyObject,
    output_dir: PathBuf,
}

#[pymethods]
impl DolphinCompiler {
    #[new]
    fn new(py: Python<'_>, frontend_path: &str, output_path: &str) -> PyResult<Self> {
        let frontend = PyModule::import(py, frontend_path)?;
        
        Ok(DolphinCompiler {
            python_frontend: frontend.into(),
            output_dir: PathBuf::from(output_path),
        })
    }

    fn compile(&self, source_code: &str) -> PyResult<()> {
        Python::with_gil(|py| {
            // Call the Python frontend to generate IR
            let ir_result = self.python_frontend
                .getattr(py, "compile_to_ir")?
                .call1(py, (source_code,))?;

            // Convert IR to Rust representation
            let ir_str: String = ir_result.extract(py)?;
            let ir = self.parse_ir(&ir_str)
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to parse IR: {}", e)))?;

            // Generate Rust code using our new generator system
            let generated_code = self.generate_anchor_program(&ir)
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to generate code: {}", e)))?;

            // Write to file
            self.write_output(&generated_code)
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to write output: {}", e)))?;

            // Call anchor build
            self.build_anchor_program()
                .map_err(|e| PyRuntimeError::new_err(format!("Anchor build failed: {}", e)))?;

            Ok(())
        })
    }
}

impl DolphinCompiler {
    fn parse_ir(&self, ir_str: &str) -> Result<IR, Box<dyn Error>> {
        serde_json::from_str(ir_str).map_err(|e| e.into())
    }

    fn generate_anchor_program(&self, ir: &IR) -> Result<String, Box<dyn Error>> {
        let mut program_code = String::new();

        // Add Anchor program attributes
        program_code.push_str(&format!(
            r#"
use anchor_lang::prelude::*;

declare_id!("{}");

#[program]
pub mod {} {{
    use super::*;
"#,
            ir.program_id,
            ir.program_name
        ));

        // Generate account structures
        for account in &ir.accounts {
            program_code.push_str(&accounts::generate_account_code(account));
        }

        // Generate instruction handlers
        for instruction in &ir.instructions {
            program_code.push_str(&instructions::generate_instruction_code(instruction));
        }

        program_code.push_str("\n} // end of program module");

        Ok(program_code)
    }

    fn write_output(&self, code: &str) -> std::io::Result<()> {
        use std::fs;
        use std::io::Write;

        let output_file = self.output_dir.join("lib.rs");
        let mut file = fs::File::create(output_file)?;
        file.write_all(code.as_bytes())?;
        Ok(())
    }

    fn build_anchor_program(&self) -> Result<(), Box<dyn Error>> {
        use std::process::Command;

        let status = Command::new("anchor")
            .arg("build")
            .current_dir(&self.output_dir)
            .status()?;

        if !status.success() {
            return Err("Anchor build failed".into());
        }
        Ok(())
    }
}