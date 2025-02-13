use pyo3::prelude::*;

#[pyclass]
#[derive(Clone)]
pub struct ProgramDefinition {
    #[pyo3(get, set)]
    pub name: String,
    #[pyo3(get, set)]
    pub version: String,
    #[pyo3(get)]
    pub description: Option<String>,
    #[pyo3(get, set)]
    pub instructions: Vec<String>,
    #[pyo3(get, set)]
    pub accounts: Vec<String>,
}

#[pymethods]
impl ProgramDefinition {
    #[new]
    fn new(name: String, version: String) -> Self {
        ProgramDefinition {
            name,
            version,
            description: None,
            instructions: Vec::new(),
            accounts: Vec::new(),
        }
    }

    fn add_instruction(&mut self, instruction: String) -> PyResult<()> {
        self.instructions.push(instruction);
        Ok(())
    }

    fn add_account(&mut self, account: String) -> PyResult<()> {
        self.accounts.push(account);
        Ok(())
    }

    fn set_description(&mut self, description: String) -> PyResult<()> {
        self.description = Some(description);
        Ok(())
    }

    fn generate_code(&self) -> PyResult<String> {
        Ok(generate_program_code(self))
    }
}

fn generate_program_code(program: &ProgramDefinition) -> String {
    let mut code = String::new();
    
    // Add program declaration
    code.push_str("use anchor_lang::prelude::*;\n\n");
    code.push_str(&format!("declare_id!(\"{}\");\n\n", "program_id_placeholder"));
    
    // Add program module
    code.push_str("#[program]\n");
    code.push_str(&format!("pub mod {} {{\n", program.name));
    code.push_str("    use super::*;\n\n");
    
    // Add instruction placeholders
    for instruction in &program.instructions {
        code.push_str(&format!("    // Include instruction: {}\n", instruction));
    }
    
    code.push_str("}\n\n");
    
    // Add account placeholders
    for account in &program.accounts {
        code.push_str(&format!("    // Include account: {}\n", account));
    }
    
    code
}

// Register the classes in the Python module
pub fn register(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ProgramDefinition>()?;
    Ok(())
}