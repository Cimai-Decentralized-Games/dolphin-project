// src/compiler/generator/instructions.rs
use pyo3::prelude::*;
use crate::compiler::ir::{Instruction, InstructionArgument as IRInstructionArgument, AccountUsage};

#[pyclass]
#[derive(Clone)]
pub struct InstructionArgument {
    #[pyo3(get, set)]
    pub name: String,
    #[pyo3(get, set)]
    pub ty: String,
}

#[pymethods]
impl InstructionArgument {
    #[new]
    fn new(name: String, ty: String) -> Self {
        InstructionArgument { name, ty }
    }
}

#[pyclass]
#[derive(Clone)]
pub struct InstructionDefinition {
    #[pyo3(get, set)]
    pub name: String,
    #[pyo3(get, set)]
    pub arguments: Vec<InstructionArgument>,
    #[pyo3(get, set)]
    pub accounts: Vec<String>,
}

#[pymethods]
impl InstructionDefinition {
    #[new]
    fn new(name: String) -> Self {
        InstructionDefinition {
            name,
            arguments: Vec::new(),
            accounts: Vec::new(),
        }
    }

    fn add_argument(&mut self, argument: InstructionArgument) -> PyResult<()> {
        self.arguments.push(argument);
        Ok(())
    }

    fn add_account(&mut self, account: String) -> PyResult<()> {
        self.accounts.push(account);
        Ok(())
    }

    fn generate_code(&self) -> PyResult<String> {
        // Convert InstructionDefinition to IR Instruction
        let instruction = Instruction {
            name: self.name.clone(),
            arguments: self.arguments.iter()
                .map(|arg| IRInstructionArgument {
                    name: arg.name.clone(),
                    ty: arg.ty.clone(),
                })
                .collect(),
            accounts: self.accounts.iter()
                .map(|account| AccountUsage {
                    name: account.clone(),
                    is_mutable: false,  // Default values
                    is_signer: false,   // Default values
                    account_type: "Account".to_string(), // Default type
                })
                .collect(),
            body: Vec::new(),
        };
        
        Ok(generate_instruction_code(&instruction))
    }
}

pub fn generate_instruction_code(instruction: &Instruction) -> String {
    let mut code = String::new();
    
    // Generate instruction function
    code.push_str("#[instruction]\n");
    code.push_str(&format!("pub fn {}(\n", instruction.name));
    code.push_str("    ctx: Context<Self>,\n");
    
    // Add arguments
    for arg in &instruction.arguments {
        code.push_str(&format!("    {}: {},\n", arg.name, arg.ty));
    }
    code.push_str(") -> Result<()> {\n");
    
    // Add basic implementation
    code.push_str("    Ok(())\n");
    code.push_str("}\n\n");
    
    // Generate Context struct
    code.push_str("#[derive(Accounts)]\n");
    code.push_str(&format!("pub struct {} {{\n", instruction.name));
    
    // Add account fields
    for account in &instruction.accounts {
        code.push_str(&format!("    pub {}: Account<'{}, {}>,\n", 
            account.name.to_lowercase(), "info", account.account_type));
    }
    
    code.push_str("}\n");
    
    code
}

// Register the classes in the Python module
pub fn register(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<InstructionArgument>()?;
    m.add_class::<InstructionDefinition>()?;
    Ok(())
}