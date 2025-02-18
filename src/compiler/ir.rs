//src/compiler/ir.rs
use serde::{Deserialize, Serialize};
use pyo3::prelude::*;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IR {
    pub program_id: String,
    pub program_name: String,
    pub program_version: String,
    pub instructions: Vec<Instruction>,
    pub accounts: Vec<Account>,
    pub types: Vec<CustomType>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Instruction {
    pub name: String,
    pub arguments: Vec<InstructionArgument>,
    pub accounts: Vec<AccountUsage>,
    pub body: Vec<Statement>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Account {
    pub name: String,
    pub fields: Vec<AccountField>,
    pub is_program_owned: bool,
    pub is_pda: bool,
    pub seeds: Vec<String>,
    pub discriminator: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountUsage {
    pub name: String,
    pub is_mutable: bool,
    pub is_signer: bool,
    pub account_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountField {
    pub name: String,
    pub ty: String,
    pub attributes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstructionArgument {
    pub name: String,
    pub ty: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromPyObject)]
pub struct Statement {
    pub kind: StatementKind,
    pub span: Span,
}

#[pyclass(module = "dolphin.compiler.ir")]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RequireData {
    #[pyo3(get)]
    pub condition: Expression,
    #[pyo3(get)]
    pub message: String,
    #[pyo3(get)]
    pub span: SpanData,
}

#[pyclass(module = "dolphin.compiler.ir")]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpanData {
    #[pyo3(get)]
    pub line: u32,
    #[pyo3(get)]
    pub column: u32,
}
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum StatementKind {
    Assignment { 
        target: String, 
        value: Expression 
    },
    MethodCall { 
        target: String, 
        method: String, 
        args: Vec<Expression> 
    },
    require { 
        data: RequireData 
    }
}

#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Expression {
    pub kind: ExpressionKind,
    pub span: Span,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExpressionKind {
    Literal(Literal),
    Variable(String),
    BinaryOp { op: String, left: Box<Expression>, right: Box<Expression> },
}

#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Literal {
    Integer(i64),
    Float(f64),
    String(String),
    Boolean(bool),
}

#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Span {
    #[pyo3(get, set)]
    pub start: usize,
    #[pyo3(get, set)]
    pub end: usize,
    #[pyo3(get, set)]
    pub line: usize,
    #[pyo3(get, set)]
    pub column: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CustomType {
    pub name: String,
    pub variants: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AccountAttribute {
    Mutable,
    Signer,
    Optional,
    ProgramOwned,
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum InstructionReturnType {
    Result,
    Option(Box<CustomType>),
    Custom(String),
}

impl IR {
    pub fn new(program_id: String, program_name: String) -> Self {
        IR {
            program_id,
            program_name,
            program_version: "0.1.0".to_string(),
            instructions: Vec::new(),
            accounts: Vec::new(),
            types: Vec::new(),
        }
    }

    pub fn add_account(&mut self, account: Account) {
        self.accounts.push(account);
    }

    pub fn add_instruction(&mut self, instruction: Instruction) {
        self.instructions.push(instruction);
    }

    pub fn add_type(&mut self, custom_type: CustomType) {
        self.types.push(custom_type);
    }
}

impl Account {
    pub fn new(name: String) -> Self {
        Account {
            name,
            fields: Vec::new(),
            is_program_owned: true,
            is_pda: false,
            seeds: Vec::new(),
            discriminator: None,
        }
    }

    pub fn add_field(&mut self, field: AccountField) {
        self.fields.push(field);
    }

    pub fn set_pda(&mut self, seeds: Vec<String>) {
        self.is_pda = true;
        self.seeds = seeds;
    }
}

impl Instruction {
    pub fn new(name: String) -> Self {
        Instruction {
            name,
            arguments: Vec::new(),
            accounts: Vec::new(),
            body: Vec::new(),
        }
    }

    pub fn add_argument(&mut self, arg: InstructionArgument) {
        self.arguments.push(arg);
    }

    pub fn add_account(&mut self, account: AccountUsage) {
        self.accounts.push(account);
    }

    pub fn add_statement(&mut self, statement: Statement) {
        self.body.push(statement);
    }
}

impl From<&crate::compiler::generator::accounts::AccountDefinition> for Account {
    fn from(py_account: &crate::compiler::generator::accounts::AccountDefinition) -> Self {
        Account {
            name: py_account.name.clone(),
            fields: py_account.fields.iter().map(AccountField::from).collect(),
            is_program_owned: true,
            is_pda: py_account.is_pda,
            seeds: py_account.seeds.clone(),
            discriminator: None,
        }
    }
}

impl From<&crate::compiler::generator::accounts::AccountField> for AccountField {
    fn from(py_field: &crate::compiler::generator::accounts::AccountField) -> Self {
        AccountField {
            name: py_field.name.clone(),
            ty: py_field.ty.clone(),
            attributes: py_field.attributes.clone(),
        }
    }
}

impl From<&crate::compiler::generator::instructions::InstructionDefinition> for Instruction {
    fn from(py_instruction: &crate::compiler::generator::instructions::InstructionDefinition) -> Self {
        Instruction {
            name: py_instruction.name.clone(),
            arguments: py_instruction.arguments.iter().map(InstructionArgument::from).collect(),
            accounts: py_instruction.accounts.iter().map(|account_str| AccountUsage {
                name: account_str.clone(),
                is_mutable: false, // Default values
                is_signer: false,  // Default values
                account_type: "Account".to_string(), // Default account type
            }).collect(),
            body: Vec::new(),
        }
    }
}


impl From<&crate::compiler::generator::instructions::InstructionArgument> for InstructionArgument {
    fn from(py_arg: &crate::compiler::generator::instructions::InstructionArgument) -> Self {
        InstructionArgument {
            name: py_arg.name.clone(),
            ty: py_arg.ty.clone(),
        }
    }
}

#[pymethods]
impl StatementKind {
    #[new]
    fn new_assignment(target: String, value: Expression) -> Self {
        StatementKind::Assignment { target, value }
    }

    #[staticmethod]
    fn method_call(target: String, method: String, args: Vec<Expression>) -> Self {
        StatementKind::MethodCall { target, method, args }
    }

    #[staticmethod]
fn require(condition: Expression, message: String, span: SpanData) -> Self {
    StatementKind::require { 
        data: RequireData {
            condition,
            message,
            span,
        }
    }
}
}

// #[pymethods]
// impl ExpressionKind {
//     #[new]
//     fn new_literal(lit: Literal) -> Self {
//         ExpressionKind::Literal(lit)
//     }

//     #[staticmethod]
//     fn variable(name: String) -> Self {
//         ExpressionKind::Variable(name)
//     }

//     #[staticmethod]
//     fn binary_op(op: String, left: Expression, right: Expression) -> Self {
//         ExpressionKind::BinaryOp {
//             op,
//             left: Box::new(left),
//             right: Box::new(right),
//         }
//     }
// }

#[pymethods]
impl RequireData {
    #[new]
    fn new(condition: Expression, message: String, span: SpanData) -> Self {
        RequireData {
            condition,
            message,
            span,
        }
    }
}

#[pymethods]
impl SpanData {
    #[new]
    fn new(line: u32, column: u32) -> Self {
        SpanData {
            line,
            column,
        }
    }
}

#[pymethods]
impl Literal {
    #[new]
    fn new_integer(value: i64) -> Self {
        Literal::Integer(value)
    }

    #[staticmethod]
    fn float(value: f64) -> Self {
        Literal::Float(value)
    }

    #[staticmethod]
    fn string(value: String) -> Self {
        Literal::String(value)
    }

    #[staticmethod]
    fn boolean(value: bool) -> Self {
        Literal::Boolean(value)
    }
}
