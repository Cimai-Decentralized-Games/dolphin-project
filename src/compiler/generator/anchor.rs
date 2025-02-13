use crate::compiler::ir::{
    Account, AccountField, Instruction, AccountUsage, Statement, 
    Expression, StatementKind, ExpressionKind, Literal
};

pub fn generate_anchor_account(account: &Account) -> String {
    let mut code = String::new();
    
    // Add Anchor attribute
    code.push_str("#[account]\n");
    if account.is_program_owned {
        code.push_str("#[derive(Default)]\n");
    }
    
    code.push_str(&format!("pub struct {} {{\n", account.name));
    
    // Generate fields
    for field in &account.fields {
        let attributes = if !field.attributes.is_empty() {
            format!("#[{}]\n    ", field.attributes.join(", "))
        } else {
            String::new()
        };
        code.push_str(&format!("    {}pub {}: {},\n", attributes, field.name, field.ty));
    }
    
    code.push_str("}\n\n");
    
    // Generate Anchor account implementation
    if account.is_program_owned {
        code.push_str(&format!(
            r#"impl {} {{
    pub fn space() -> usize {{
        8 + {} // 8 bytes for the account discriminator
    }}
"#,
            account.name,
            calculate_account_space(account)
        ));
        
        code.push_str("}\n");
    }
    
    code
}

pub fn generate_anchor_instruction(instruction: &Instruction) -> String {
    let mut code = String::new();
    
    // Generate Anchor context struct
    code.push_str(&format!(
        r#"#[derive(Accounts)]
pub struct {}Context<'info> {{
"#,
        instruction.name
    ));
    
    // Add account constraints
    for account in &instruction.accounts {
        let mut constraints = Vec::new();
        if account.is_mutable {
            constraints.push("mut");
        }
        if account.is_signer {
            constraints.push("signer");
        }
        
        let constraint_str = if !constraints.is_empty() {
            format!("#[account({})]\n    ", constraints.join(", "))
        } else {
            "".to_string()
        };
        
        code.push_str(&format!(
            "    {}pub {}: Account<'info, {}>,\n",
            constraint_str,
            account.name,
            account.account_type
        ));
    }
    
    code.push_str("}\n\n");
    
    // Generate instruction handler
    code.push_str(&format!(
        r#"pub fn {}(ctx: Context<{}Context>{}) -> Result<()> {{
"#,
        instruction.name,
        instruction.name,
        if instruction.arguments.is_empty() {
            "".to_string()
        } else {
            format!(
                ", {}",
                instruction.arguments
                    .iter()
                    .map(|arg| format!("{}: {}", arg.name, arg.ty))
                    .collect::<Vec<_>>()
                    .join(", ")
            )
        }
    ));
    
    // Add instruction body
    code.push_str(&generate_instruction_body(&instruction.body));
    code.push_str("    Ok(())\n}\n\n");
    
    code
}

fn calculate_account_space(account: &Account) -> usize {
    let mut space = 0;
    for field in &account.fields {
        space += match field.ty.as_str() {
            "u8" => 1,
            "u16" => 2,
            "u32" => 4,
            "u64" => 8,
            "i8" => 1,
            "i16" => 2,
            "i32" => 4,
            "i64" => 8,
            "bool" => 1,
            "Pubkey" => 32,
            // Add more types as needed
            _ => 8, // Default size for unknown types
        };
    }
    space
}

fn generate_instruction_body(statements: &[Statement]) -> String {
    let mut code = String::new();
    
    for statement in statements {
        match &statement.kind {
            StatementKind::Assignment { target, value } => {
                code.push_str(&format!("    {} = {};\n", target, generate_expression(value)));
            },
            StatementKind::MethodCall { target, method, args } => {
                let args_str = args.iter()
                    .map(generate_expression)
                    .collect::<Vec<_>>()
                    .join(", ");
                code.push_str(&format!("    {}.{}({});\n", target, method, args_str));
            },
        }
    }
    
    code
}

fn generate_expression(expr: &Expression) -> String {
    match &expr.kind {
        ExpressionKind::Literal(lit) => match lit {
            Literal::Integer(i) => i.to_string(),
            Literal::Float(f) => f.to_string(),
            Literal::String(s) => format!("\"{}\"", s),
            Literal::Boolean(b) => b.to_string(),
        },
        ExpressionKind::Variable(name) => name.clone(),
        ExpressionKind::BinaryOp { op, left, right } => {
            format!("({} {} {})", 
                generate_expression(left), 
                op, 
                generate_expression(right)
            )
        },
    }
}
