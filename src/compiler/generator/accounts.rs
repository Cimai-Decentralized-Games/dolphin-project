// src/compiler/generator/accounts.rs
use pyo3::prelude::*;
use crate::compiler::ir::Account; // Specific import for Account type

#[pyclass]
#[derive(Clone)]
pub struct AccountField {
    #[pyo3(get, set)]
    pub name: String,
    #[pyo3(get, set)]
    pub ty: String,
    #[pyo3(get, set)]
    pub attributes: Vec<String>,
}

#[pymethods]
impl AccountField {
    #[new]
    fn new(name: String, ty: String) -> Self {
        AccountField {
            name,
            ty,
            attributes: Vec::new(),
        }
    }

    fn add_attribute(&mut self, attribute: String) -> PyResult<()> {
        self.attributes.push(attribute);
        Ok(())
    }
}

#[pyclass]
#[derive(Clone)]
pub struct AccountDefinition {
    #[pyo3(get, set)]
    pub name: String,
    #[pyo3(get, set)]
    pub fields: Vec<AccountField>,
    #[pyo3(get, set)]
    pub is_pda: bool,
    #[pyo3(get, set)]
    pub seeds: Vec<String>,
}

#[pymethods]
impl AccountDefinition {
    #[new]
    fn new(name: String) -> Self {
        AccountDefinition {
            name,
            fields: Vec::new(),
            is_pda: false,
            seeds: Vec::new(),
        }
    }

    fn add_field(&mut self, field: AccountField) -> PyResult<()> {
        self.fields.push(field);
        Ok(())
    }

    fn set_as_pda(&mut self, seeds: Vec<String>) -> PyResult<()> {
        self.is_pda = true;
        self.seeds = seeds;
        Ok(())
    }

    fn generate_code(&self) -> PyResult<String> {
        // Convert AccountDefinition to Account
        let account = Account {
            name: self.name.clone(),
            fields: self.fields.iter().map(|f| crate::compiler::ir::AccountField {
                name: f.name.clone(),
                ty: f.ty.clone(),
                attributes: f.attributes.clone(),
            }).collect(),
            is_program_owned: true,
            is_pda: self.is_pda,
            seeds: self.seeds.clone(),
            discriminator: None,
        };
        
        Ok(generate_account_code(&account))
    }
}

pub fn generate_account_code(account: &Account) -> String {
    let mut code = String::new();
    
    // Add derives
    code.push_str("#[account]\n");
    code.push_str("#[derive(Default)]\n");
    
    // Generate struct
    code.push_str(&format!("pub struct {} {{\n", account.name));
    
    // Generate fields
    for field in &account.fields {
        if !field.attributes.is_empty() {
            code.push_str(&format!("    #[{}]\n", field.attributes.join(", ")));
        }
        code.push_str(&format!("    pub {}: {},\n", field.name, field.ty));
    }
    
    code.push_str("}\n\n");
    
    // Generate impl block if PDA
    if account.is_pda {
        code.push_str(&format!("impl {} {{\n", account.name));
        code.push_str("    pub fn seeds() -> &'static [&'static [u8]] {\n");
        code.push_str("        &[\n");
        for seed in &account.seeds {
            code.push_str(&format!("            b\"{}\",\n", seed));
        }
        code.push_str("        ]\n    }\n}\n");
    }
    
    code
}

// Register the classes in the Python module
pub fn register(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<AccountField>()?;
    m.add_class::<AccountDefinition>()?;
    Ok(())
}