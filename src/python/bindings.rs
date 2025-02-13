use pyo3::prelude::*;
use crate::compiler::ir::{
    Account, Instruction, AccountField, InstructionArgument, 
    AccountUsage, Statement, StatementKind, Span
};
use crate::compiler::generator;

#[pyclass]
pub struct AccountGenerator {
    inner: Account,
}

#[pymethods]
impl AccountGenerator {
    #[new]
    fn new(name: String) -> Self {
        Self {
            inner: Account {
                name,
                fields: Vec::new(),
                is_program_owned: true,
                is_pda: false,
                seeds: Vec::new(),
                discriminator: None,
            }
        }
    }

    fn generate_account(&self) -> PyResult<String> {
        Ok(generator::anchor::generate_anchor_account(&self.inner))
    }

    fn add_field(&mut self, name: String, ty: String, attributes: Vec<String>) -> PyResult<()> {
        self.inner.fields.push(AccountField {
            name,
            ty,
            attributes,
        });
        Ok(())
    }

    fn set_pda(&mut self, seeds: Vec<String>) -> PyResult<()> {
        self.inner.is_pda = true;
        self.inner.seeds = seeds;
        Ok(())
    }

    #[pyo3(signature = (discriminator=None))]
    fn set_discriminator(&mut self, discriminator: Option<String>) -> PyResult<()> {
        self.inner.discriminator = discriminator;
        Ok(())
    }
}

#[pyclass]
pub struct InstructionGenerator {
    inner: Instruction,
}

#[pymethods]
impl InstructionGenerator {
    #[new]
    fn new(name: String) -> Self {
        Self {
            inner: Instruction {
                name,
                arguments: Vec::new(),
                accounts: Vec::new(),
                body: Vec::new(),
            }
        }
    }

    fn generate_instruction(&self) -> PyResult<String> {
        Ok(generator::anchor::generate_anchor_instruction(&self.inner))
    }

    fn add_argument(&mut self, name: String, ty: String) -> PyResult<()> {
        self.inner.arguments.push(InstructionArgument {
            name,
            ty,
        });
        Ok(())
    }

    fn add_account(&mut self, name: String, is_mutable: bool, is_signer: bool, account_type: String) -> PyResult<()> {
        self.inner.accounts.push(AccountUsage {
            name,
            is_mutable,
            is_signer,
            account_type,
        });
        Ok(())
    }

    fn add_statement(&mut self, kind: StatementKind, start: usize, end: usize, line: usize, column: usize) -> PyResult<()> {
        let span = Span {
            start,
            end,
            line,
            column,
        };
        
        let statement = Statement {
            kind,
            span,
        };
        
        self.inner.body.push(statement);
        Ok(())
    }
}

#[pyclass]
pub struct ProgramGenerator {
    program_id: String,
    program_name: String,
    version: String,
    accounts: Vec<Account>,
    instructions: Vec<Instruction>,
}

#[pymethods]
impl ProgramGenerator {
    #[new]
    fn new(program_id: String, program_name: String) -> Self {
        Self {
            program_id,
            program_name,
            version: "0.1.0".to_string(),
            accounts: Vec::new(),
            instructions: Vec::new(),
        }
    }

    fn add_account(&mut self, account: &AccountGenerator) -> PyResult<()> {
        self.accounts.push(account.inner.clone());
        Ok(())
    }

    fn add_instruction(&mut self, instruction: &InstructionGenerator) -> PyResult<()> {
        self.instructions.push(instruction.inner.clone());
        Ok(())
    }

    fn generate_program(&self) -> PyResult<String> {
        let mut code = format!(
            r#"use anchor_lang::prelude::*;

declare_id!("{}");

#[program]
pub mod {} {{
    use super::*;

"#,
            self.program_id, self.program_name
        );

        // Generate accounts
        for account in &self.accounts {
            code.push_str(&generator::anchor::generate_anchor_account(account));
        }

        // Generate instructions
        for instruction in &self.instructions {
            code.push_str(&generator::anchor::generate_anchor_instruction(instruction));
        }

        code.push_str("}\n");
        Ok(code)
    }

    fn set_version(&mut self, version: String) -> PyResult<()> {
        self.version = version;
        Ok(())
    }
}

pub fn init_module(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<AccountGenerator>()?;
    m.add_class::<InstructionGenerator>()?;
    m.add_class::<ProgramGenerator>()?;
    Ok(())
}
