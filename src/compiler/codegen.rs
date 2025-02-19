use super::ir::{
    IR, Instruction, Account, Statement, Expression, StatementKind,
    RequireData, ExpressionKind, Literal, CustomType
};
use std::error::Error;

#[derive(Debug)]
pub struct CodeGenerator {
    ir: IR,
}

impl CodeGenerator {
    pub fn new(ir: IR) -> Self {
        CodeGenerator { ir }
    }

    pub fn generate(&self) -> Result<String, Box<dyn Error>> {
        let mut code = String::new();

        // Generate program module
        code.push_str(&self.generate_program_header());
        
        // Generate custom types
        for custom_type in &self.ir.types {
            code.push_str(&self.generate_custom_type(custom_type));
        }
        
        // Generate account structures
        for account in &self.ir.accounts {
            code.push_str(&self.generate_account(account));
        }

        // Generate instruction handlers
        for instruction in &self.ir.instructions {
            code.push_str(&self.generate_instruction(instruction));
        }

        code.push_str("\n} // mod program\n");
        Ok(code)
    }

    fn generate_program_header(&self) -> String {
        format!(
            r#"use anchor_lang::prelude::*;
use anchor_lang::solana_program::system_program;

declare_id!("{}");

#[program]
pub mod {} {{
    use super::*;

"#,
            self.ir.program_id,
            self.ir.program_name.to_lowercase()
        )
    }

    fn generate_account(&self, account: &Account) -> String {
        let mut code = String::new();
        
        // Generate account attributes
        code.push_str("    #[account]\n");
        code.push_str("    #[derive(Default)]\n");
        if account.is_pda {
            // Generate seeds attribute
            let seeds = account.seeds.iter()
                .map(|seed| {
                    if seed.starts_with('"') && seed.ends_with('"') {
                        // For string literals, format as byte string
                        let inner = &seed[1..seed.len()-1]; // Remove outer quotes
                        format!("b\"{}\"", inner)
                    } else {
                        // For variables, use as_ref() for Pubkey references
                        format!("{}.as_ref()", seed)
                    }
                })
                .collect::<Vec<_>>()
                .join(", ");
            code.push_str(&format!("    #[seeds = [{}]]\n", seeds));
            
            // Add bump attribute for PDA accounts
            code.push_str("    #[bump]\n");
        }
        
        // Generate struct
        code.push_str(&format!("    pub struct {} {{\n", account.name));
        
        // Generate fields in correct order for PDA accounts
        if account.is_pda {
            // First generate the fields used as seeds
            for seed in &account.seeds {
                if !seed.starts_with('"') {
                    // This is a field reference, find its type
                    if let Some(field) = account.fields.iter().find(|f| f.name == *seed) {
                        let attrs = if !field.attributes.is_empty() {
                            format!("        {}\n", field.attributes.join(" "))
                        } else {
                            String::new()
                        };
                        code.push_str(&format!("{}        pub {}: {},\n", 
                            attrs, field.name, field.ty));
                    }
                }
            }
            
            // Then generate bump
            code.push_str("        /// The bump used to generate the PDA\n");
            code.push_str("        pub bump: u8,\n");
            
            // Then generate remaining fields that weren't used as seeds
            for field in &account.fields {
                if !account.seeds.iter().any(|seed| !seed.starts_with('"') && *seed == field.name) {
                    let attrs = if !field.attributes.is_empty() {
                        format!("        {}\n", field.attributes.join(" "))
                    } else {
                        String::new()
                    };
                    code.push_str(&format!("{}        pub {}: {},\n", 
                        attrs, field.name, field.ty));
                }
            }
        } else {
            // For non-PDA accounts, generate fields in original order
            for field in &account.fields {
                let attrs = if !field.attributes.is_empty() {
                    format!("        {}\n", field.attributes.join(" "))
                } else {
                    String::new()
                };
                code.push_str(&format!("{}        pub {}: {},\n", 
                    attrs, field.name, field.ty));
            }
        }
        
        code.push_str("    }\n\n");
        if account.is_pda {
            code.push_str(&format!("    impl {} {{\n", account.name));
            code.push_str("        /// Generates the PDA for this account\n");
            code.push_str("        pub fn generate_pda(\n");
            code.push_str("            &self,\n");
            code.push_str("            program_id: &Pubkey,\n");
            code.push_str("        ) -> Result<(Pubkey, u8)> {\n");
            code.push_str("            let seeds: &[&[u8]] = &[\n");
            for seed in &account.seeds {
                if seed.starts_with('"') && seed.ends_with('"') {
                    // String literals become byte strings
                    let inner = &seed[1..seed.len()-1];
                    code.push_str(&format!("                b\"{}\",\n", inner));
                } else {
                    // Field references use to_bytes()
                    code.push_str(&format!("                &self.{}.to_bytes(),\n", seed));
                }
            }
            code.push_str("                &[self.bump],\n");  // Add bump as final seed
            code.push_str("            ];\n");
            code.push_str("            Pubkey::find_program_address(seeds, program_id)\n");
            code.push_str("        }\n");
            code.push_str("    }\n\n");
        }
        code
    }
    

    fn generate_instruction(&self, instruction: &Instruction) -> String {
        let mut code = String::new();
        
        // Generate context struct
        code.push_str(&self.generate_instruction_context(instruction));
        
        // Generate handler function
        code.push_str(&format!("    pub fn {}(\n", instruction.name));
        code.push_str("        ctx: Context<Self>,\n");
        
        // Generate arguments
        for arg in &instruction.arguments {
            code.push_str(&format!("        {}: {},\n", 
                arg.name, arg.ty));
        }
        
        code.push_str("    ) -> Result<()> {\n");
        
        // Generate body
        for stmt in &instruction.body {
            code.push_str(&self.generate_statement(stmt));
        }
        
        code.push_str("        Ok(())\n    }\n\n");
        code
    }

    fn generate_statement(&self, stmt: &Statement) -> String {
        let indent = "        ";
        match &stmt.kind {
            StatementKind::Require { data } => {
                self.generate_require(data)
            },
            StatementKind::Assignment { target, value } => {
                format!("{}{} = {};\n",
                    indent,
                    target,
                    self.generate_expression(value)
                )
            },
            StatementKind::MethodCall { target, method, args } => {
                let args_str = args.iter()
                    .map(|arg| self.generate_expression(arg))
                    .collect::<Vec<_>>()
                    .join(", ");
                format!("{}{}.{}({});\n",
                    indent,
                    target, 
                    method,
                    args_str
                )
            }
        }
    }

    fn generate_require(&self, data: &RequireData) -> String {
        let indent = "        ";
        format!("{}require!({}, \"{}\");\n",
            indent,
            self.generate_expression(&data.condition),
            data.message
        )
    }

    fn generate_expression(&self, expr: &Expression) -> String {
        match &expr.kind {
            ExpressionKind::Literal(lit) => self.generate_literal(lit),
            ExpressionKind::Variable(name) => name.clone(),
            ExpressionKind::BinaryOp { op, left, right } => {
                format!("({} {} {})",
                    self.generate_expression(left),
                    op,
                    self.generate_expression(right)
                )
            },
            ExpressionKind::List(elements) => {
                let elements_str = elements.iter()
                    .map(|elem| self.generate_expression(elem))
                    .collect::<Vec<_>>()
                    .join(", ");
                format!("[{}]", elements_str)
            }
        }
    }

    fn generate_literal(&self, lit: &Literal) -> String {
        match lit {
            Literal::Integer(n) => n.to_string(),
            Literal::Float(f) => f.to_string(),
            Literal::String(s) => format!("\"{}\"", s),
            Literal::Boolean(b) => b.to_string(),
        }
    }

    fn generate_instruction_context(&self, instruction: &Instruction) -> String {
        let mut code = String::new();
        
        code.push_str("    #[derive(Accounts)]\n");
        code.push_str(&format!("    pub struct {} {{\n", instruction.name));
        
        // Generate account fields
        for account in &instruction.accounts {
            let mut attrs = vec![];
            if account.is_mutable {
                attrs.push("mut");
            }
            if account.is_signer {
                attrs.push("signer");
            }
            
            let attr_str = if !attrs.is_empty() {
                format!("        #[account({})]\n", attrs.join(", "))
            } else {
                String::new()
            };
            
            code.push_str(&attr_str);
            code.push_str(&format!("        pub {}: Account<'info, {}>,\n",
                account.name,
                account.account_type
            ));
        }
        
        code.push_str("    }\n\n");
        code
    }

    fn generate_custom_type(&self, custom_type: &CustomType) -> String {
        let mut code = String::new();
        
        if !custom_type.variants.is_empty() {
            // Generate enum
            code.push_str("    #[derive(AnchorSerialize, AnchorDeserialize)]\n");
            code.push_str(&format!("    pub enum {} {{\n", custom_type.name));
            
            for variant in &custom_type.variants {
                code.push_str(&format!("        {},\n", variant));
            }
            
            code.push_str("    }\n\n");
        }
        
        code
    }
}
