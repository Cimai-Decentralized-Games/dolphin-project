use anchor_lang::prelude::*;

declare_id!("Test111111111111111111111111111111111111111");

#[program]
pub mod TestProgram {
    use super::*;

#[account]
#[derive(Default)]
pub struct Counter {
    pub authority: Pubkey,
    pub count: u64,
}

impl Counter {
    pub fn space() -> usize {
        8 + 40 // 8 bytes for the account discriminator
    }
}
#[derive(Accounts)]
pub struct initializeContext<'info> {
}

pub fn initialize(ctx: Context<initializeContext>, authority: Pubkey) -> Result<()> {
    Ok(())
}

#[derive(Accounts)]
pub struct incrementContext<'info> {
}

pub fn increment(ctx: Context<incrementContext>) -> Result<()> {
    Ok(())
}

}
