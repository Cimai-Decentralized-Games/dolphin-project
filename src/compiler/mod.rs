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
use crate::compiler::codegen::CodeGenerator;

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
        let frontend = PyModule::import(py, "dolphin.parser")?;
        
        Ok(DolphinCompiler {
            python_frontend: frontend.into(),
            output_dir: PathBuf::from(output_path),
        })
    }

    fn compile(&self, ir_program: PyObject) -> PyResult<()> {
        Python::with_gil(|py| {
            // Convert IRProgram to JSON string using json.dumps()
            let json = PyModule::import(py, "json")?;
            let to_json = PyModule::import(py, "dolphin.ir")?.getattr("to_json")?;
            
            let ir_dict = to_json.call1((ir_program,))
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to convert IR to dict: {}", e)))?;
            
            let ir_str = json.getattr("dumps")?.call1((ir_dict,))
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to serialize IR to JSON: {}", e)))?
                .extract::<String>()
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to extract JSON string: {}", e)))?;

            // Parse IR from JSON
            let ir = self.parse_ir(&ir_str)
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to parse IR: {}", e)))?;

            // Generate Rust code using our new generator system
            let generated_code = self.generate_anchor_program(&ir)
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to generate code: {}", e)))?;

            // Write to file
            self.write_output(&generated_code, &ir)
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
        serde_json::from_str(ir_str).map_err(|e| Box::<dyn Error>::from(e))
    }

    fn generate_anchor_program(&self, ir: &IR) -> Result<String, Box<dyn Error>> {
        let generator = CodeGenerator::new(ir.clone());
        generator.generate()
    }

    fn write_output(&self, code: &str, ir: &IR) -> Result<(), Box<dyn Error>> {
        use std::fs;
        use std::io::Write;

        // Create src directory
        let src_dir = self.output_dir.join("src");
        fs::create_dir_all(&src_dir).map_err(|e| Box::<dyn Error>::from(e))?;

        // Write lib.rs
        let output_file = src_dir.join("lib.rs");
        let mut file = fs::File::create(&output_file).map_err(|e| Box::<dyn Error>::from(e))?;
        file.write_all(code.as_bytes()).map_err(|e| Box::<dyn Error>::from(e))?;

        // Write Cargo.toml with program name from IR
        let cargo_toml = self.output_dir.join("Cargo.toml");
        let program_name = ir.program_name.to_lowercase().replace(" ", "_");
        let cargo_content = format!(r#"[package]
name = "{}_program"
version = "0.1.0"
description = "Created with Dolphin"
edition = "2021"

[lib]
crate-type = ["cdylib", "lib"]

[profile.release]
overflow-checks = true

[features]
no-entrypoint = []
no-idl = []
cpi = ["no-entrypoint"]

[dependencies]
anchor-lang = "0.30.1"
"#, program_name);

        fs::write(&cargo_toml, cargo_content).map_err(|e| Box::<dyn Error>::from(e))?;

        // Write Anchor.toml with program ID from IR
        let anchor_toml = self.output_dir.join("Anchor.toml");
        let anchor_content = format!(r#"[features]
seeds = false

[programs.devnet]
{}_program = "{}"

[workspace]
members = []

[registry]
url = "https://api.apr.dev"

[provider]
cluster = "devnet"
wallet = "~/.config/solana/id.json"
"#, program_name, ir.program_id);

        fs::write(&anchor_toml, anchor_content).map_err(|e| Box::<dyn Error>::from(e))?;

        Ok(())
    }

    fn build_anchor_program(&self) -> Result<(), Box<dyn Error>> {
        use std::process::Command;

        let output = Command::new("anchor")
            .arg("build")
            .current_dir(&self.output_dir)
            .output()
            .map_err(|e| Box::<dyn Error>::from(e))?;

        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            return Err(format!("Anchor build failed: {}", error_msg).into());
        }
        Ok(())
    }
    
}