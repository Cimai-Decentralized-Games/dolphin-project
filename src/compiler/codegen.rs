// src/compiler/codegen.rs
use super::ir::{IR, Instruction, Account, Statement, Expression};
use std::error::Error;

pub fn generate_rust_code(ir: &IR) -> Result<String, Box<dyn Error>> {
    let mut code = String::new();

    // Generate program module
    code.push_str(&generate_program_header(&ir.program_name));
    
    // Generate account structures
    for account in &ir.accounts {
        code.push_str(&generate_account(account));
    }

    // Generate instruction handlers
    for instruction in &ir.instructions {
        code.push_str(&generate_instruction(instruction));
    }

    Ok(code)
}

fn generate_program_header(program_name: &str) -> String {
    format!(
        r#"use anchor_lang::prelude::*;

declare_id!("{}");

#[program]
pub mod {} {{
    use super::*;

"#,
        program_name, program_name
    )
}

fn generate_account(account: &Account) -> String {
    let mut code = String::new();
    
    code.push_str("#[account]\n");
    code.push_str(&format!("pub struct {} {{\n", account.name));
    
    for field in &account.fields {
        code.push_str(&format!("    pub {}: {},\n", field.name, field.ty));
    }
    
    code.push_str("}\n\n");
    code
}

fn generate_instruction(instruction: &Instruction) -> String {
    let mut code = String::new();
    
    // Generate function signature
    code.push_str(&format!("    pub fn {}(\n", instruction.name));
    code.push_str("        ctx: Context<Self>,\n");
    
    // Generate arguments
    for arg in &instruction.arguments {
        code.push_str(&format!("        {}: {},\n", arg.name, arg.ty));
    }
    code.push_str("    ) -> Result<()> {\n");
    
    // Generate function body
    for stmt in &instruction.body {
        code.push_str(&generate_statement(stmt));
    }
    
    code.push_str("        Ok(())\n    }\n\n");
    code
}

fn generate_statement(stmt: &Statement) -> String {
    // Implementation for statement generation
    // This would handle different types of statements and generate appropriate Rust code
    String::new() // Placeholder
}